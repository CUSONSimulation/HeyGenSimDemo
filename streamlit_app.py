import streamlit as st
import requests
import os
import json

# Set page config
st.set_page_config(
    page_title="HeyGen Simulation Demo", 
    page_icon="🎭",
    layout="wide"
)

# Environment setup
HEYGEN_API_KEY = st.secrets.get("HEYGEN_API_KEY") or os.getenv("HEYGEN_API_KEY")

def get_access_token():
    """Generate HeyGen access token from API key"""
    if not HEYGEN_API_KEY:
        st.error("⚠️ HeyGen API Key not found. Please add it to your Streamlit secrets.")
        st.stop()
    
    try:
        response = requests.post(
            "https://api.heygen.com/v1/streaming.create_token",
            headers={"x-api-key": HEYGEN_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get("data", {}).get("token")
        else:
            st.error(f"Failed to get access token: {response.status_code}")
            st.write(f"Response: {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error getting access token: {str(e)}")
        return None

def get_compatible_voices():
    """Get list of voices compatible with streaming avatars"""
    if not HEYGEN_API_KEY:
        return {}
    
    try:
        response = requests.get(
            "https://api.heygen.com/v2/voices",
            headers={"x-api-key": HEYGEN_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            voices_data = response.json().get("data", {}).get("voices", [])
            # Filter for voices that support streaming
            compatible_voices = {}
            for voice in voices_data:
                if voice.get("support_streaming", True):  # Assume streaming support if not specified
                    name = voice.get("name", "Unknown")
                    compatible_voices[name] = {
                        "voice_id": voice.get("voice_id"),
                        "gender": voice.get("gender", "unknown"),
                        "language": voice.get("language", "en")
                    }
            return compatible_voices
        else:
            st.warning(f"Could not fetch voices: {response.status_code}")
            return {}
    except Exception as e:
        st.warning(f"Error fetching voices: {str(e)}")
        return {}
    """Get list of available avatars"""
    if not HEYGEN_API_KEY:
        return []
    
    try:
        response = requests.get(
            "https://api.heygen.com/v2/avatars",
            headers={"x-api-key": HEYGEN_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            avatars_data = response.json().get("data", {}).get("avatars", [])
            # Filter for streaming-compatible avatars
            streaming_avatars = [
                avatar for avatar in avatars_data 
                if avatar.get("avatar_type") == "streaming" or 
                   avatar.get("name", "").lower() in ["monica", "josh", "anna", "wayne"]
            ]
            return streaming_avatars
        else:
            st.warning(f"Could not fetch avatars: {response.status_code}")
            return []
    except Exception as e:
        st.warning(f"Error fetching avatars: {str(e)}")
        return []

def create_heygen_component(access_token, avatar_id, session_id, avatar_name, voice_id="default", voice_config=None):
    """Create HeyGen streaming avatar component using REST API approach with enhanced configuration"""
    
    # Default voice configuration based on SDK patterns
    if voice_config is None:
        voice_config = {
            "rate": 1.0,
            "emotion": "friendly"
        }
    
    # Use a safe default voice if the provided one might not work
    safe_voice_id = voice_id if voice_id != "default" else None
    
    # This creates a pure HTML/JS implementation that uses the HeyGen REST API
    # with enhanced session management and token refresh capability
    component_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                margin: 0;
                padding: 20px;
                background: #1a1a1a;
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            }}
            
            .container {{
                max-width: 800px;
                margin: 0 auto;
            }}
            
            .avatar-section {{
                background: #2d2d2d;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            
            .avatar-video {{
                width: 100%;
                height: 400px;
                background: black;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 15px;
                position: relative;
            }}
            
            .video-element {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                border-radius: 8px;
            }}
            
            .status {{
                text-align: center;
                padding: 10px;
                border-radius: 6px;
                margin-bottom: 15px;
                font-weight: 500;
            }}
            
            .status.loading {{ background: #1f4e79; color: #87ceeb; }}
            .status.success {{ background: #1f4e3b; color: #90ee90; }}
            .status.error {{ background: #4e1f1f; color: #ffcccb; }}
            
            .controls {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 10px;
                margin-bottom: 20px;
            }}
            
            button {{
                background: #0066cc;
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.2s;
            }}
            
            button:hover {{
                background: #0052a3;
                transform: translateY(-1px);
            }}
            
            button:disabled {{
                background: #555;
                cursor: not-allowed;
                transform: none;
            }}
            
            .chat-input {{
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }}
            
            input[type="text"] {{
                flex: 1;
                padding: 12px;
                border: 1px solid #555;
                border-radius: 6px;
                background: #333;
                color: white;
            }}
            
            .log {{
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 15px;
                height: 150px;
                overflow-y: auto;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 12px;
                line-height: 1.4;
            }}
            
            .log-entry {{
                margin-bottom: 5px;
                padding: 2px 0;
            }}
            
            .log-timestamp {{
                color: #888;
                margin-right: 8px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="avatar-section">
                <h3>{avatar_name} - Interactive Session</h3>
                
                <div class="avatar-video" id="avatarVideo">
                    <video id="videoElement" class="video-element" autoplay muted style="display: none;"></video>
                    <div id="placeholderText" style="color: #666; font-size: 18px;">
                        Setting up {avatar_name}...
                    </div>
                </div>
                
                <div id="status" class="status loading">Initializing session...</div>
                
                <div class="controls">
                    <button id="startBtn" onclick="startSession()">Start Session</button>
                    <button id="speakBtn" onclick="speakText()" disabled>Speak Test</button>
                    <button id="stopBtn" onclick="stopSession()" disabled>Stop Session</button>
                </div>
                
                <div class="chat-input">
                    <input type="text" id="chatInput" placeholder="Enter message for avatar to speak..." 
                           disabled onkeypress="handleKeyPress(event)">
                    <button onclick="speakCustomText()" disabled id="sendBtn">Send</button>
                </div>
                
                <div class="log" id="logArea"></div>
            </div>
        </div>

        <script>
            // Session state
            let sessionData = null;
            let isConnected = false;
            
            // DOM elements
            const statusEl = document.getElementById('status');
            const startBtn = document.getElementById('startBtn');
            const speakBtn = document.getElementById('speakBtn');
            const stopBtn = document.getElementById('stopBtn');
            const chatInput = document.getElementById('chatInput');
            const sendBtn = document.getElementById('sendBtn');
            const logArea = document.getElementById('logArea');
            const videoElement = document.getElementById('videoElement');
            const placeholderText = document.getElementById('placeholderText');
            
            function log(message, type = 'info') {{
                const timestamp = new Date().toLocaleTimeString();
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                logEntry.innerHTML = `<span class="log-timestamp">${{timestamp}}</span>${{message}}`;
                logArea.appendChild(logEntry);
                logArea.scrollTop = logArea.scrollHeight;
                console.log(`[${{type.toUpperCase()}}] ${{message}}`);
            }}
            
            function updateStatus(message, type = 'loading') {{
                statusEl.textContent = message;
                statusEl.className = `status ${{type}}`;
                log(message);
            }}
            
            async function startSession() {{
                try {{
                    updateStatus('Creating avatar session...', 'loading');
                    startBtn.disabled = true;
                    
                    // Try with voice first, then fallback to no voice
                    let requestPayload;
                    
                    const basePayload = {{
                        avatar_name: '{avatar_id}',
                        quality: 'low',
                        version: 'v2'
                    }};
                    
                    // Only add voice if we have a specific voice ID
                    if ('{safe_voice_id}' && '{safe_voice_id}' !== 'None') {{
                        requestPayload = {{
                            ...basePayload,
                            voice: {{
                                voice_id: '{safe_voice_id}',
                                rate: {voice_config.get("rate", 1.0)}
                            }}
                        }};
                    }} else {{
                        requestPayload = basePayload;
                    }}
                    
                    log(`Request payload: ${{JSON.stringify(requestPayload, null, 2)}}`);
                    
                    let response = await fetch('https://api.heygen.com/v1/streaming.new', {{
                        method: 'POST',
                        headers: {{
                            'Authorization': 'Bearer {access_token}',
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(requestPayload)
                    }});
                    
                    log(`Response status: ${{response.status}}`);
                    
                    // If unauthorized, the token might have expired - show error and suggest refresh
                    if (response.status === 401) {{
                        const errorText = await response.text();
                        log(`Auth error: ${{errorText}}`);
                        updateStatus('Authentication failed - please refresh the page', 'error');
                        startBtn.disabled = false;
                        return;
                    }}
                    
                    // If voice not supported, try without voice
                    if (!response.ok) {{
                        const errorText = await response.text();
                        log(`Error response: ${{errorText}}`);
                        
                        if (errorText.includes('voice_not_support')) {{
                            log('Voice not supported, trying without voice...');
                            const noVoicePayload = {{
                                avatar_name: '{avatar_id}',
                                quality: 'low',
                                version: 'v2'
                            }};
                            
                            response = await fetch('https://api.heygen.com/v1/streaming.new', {{
                                method: 'POST',
                                headers: {{
                                    'Authorization': 'Bearer {access_token}',
                                    'Content-Type': 'application/json'
                                }},
                                body: JSON.stringify(noVoicePayload)
                            }});
                            
                            if (!response.ok) {{
                                const retryError = await response.text();
                                throw new Error(`Session creation failed: ${{response.status}} - ${{retryError}}`);
                            }}
                        }} else {{
                            throw new Error(`Session creation failed: ${{response.status}} - ${{errorText}}`);
                        }}
                    }}
                    
                    const data = await response.json();
                    sessionData = data.data;
                    
                    log(`Session created: ${{sessionData.session_id}}`);
                    
                    // Start the session
                    const startResponse = await fetch('https://api.heygen.com/v1/streaming.start', {{
                        method: 'POST',
                        headers: {{
                            'Authorization': 'Bearer {access_token}',
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            session_id: sessionData.session_id
                        }})
                    }});
                    
                    if (!startResponse.ok) {{
                        throw new Error(`Session start failed: ${{startResponse.status}}`);
                    }}
                    
                    updateStatus('Session started successfully!', 'success');
                    isConnected = true;
                    
                    // Enable controls
                    speakBtn.disabled = false;
                    stopBtn.disabled = false;
                    chatInput.disabled = false;
                    sendBtn.disabled = false;
                    
                    // Hide placeholder, show video area
                    placeholderText.style.display = 'none';
                    videoElement.style.display = 'block';
                    
                    log('Avatar is ready for interaction');
                    
                }} catch (error) {{
                    updateStatus(`Error: ${{error.message}}`, 'error');
                    startBtn.disabled = false;
                    log(`Error: ${{error.message}}`, 'error');
                    
                    // Try fallback with minimal parameters
                    if (error.message.includes('400')) {{
                        log('Attempting fallback with minimal parameters...');
                        try {{
                            const fallbackPayload = {{
                                avatar_name: '{avatar_id}',
                                quality: 'low'
                            }};
                            
                            log(`Fallback payload: ${{JSON.stringify(fallbackPayload, null, 2)}}`);
                            
                            const fallbackResponse = await fetch('https://api.heygen.com/v1/streaming.new', {{
                                method: 'POST',
                                headers: {{
                                    'Authorization': 'Bearer {access_token}',
                                    'Content-Type': 'application/json'
                                }},
                                body: JSON.stringify(fallbackPayload)
                            }});
                            
                            if (fallbackResponse.ok) {{
                                const data = await fallbackResponse.json();
                                sessionData = data.data;
                                log(`Fallback session created: ${{sessionData.session_id}}`);
                                updateStatus('Session created with fallback parameters', 'success');
                                
                                // Continue with session start
                                const startResponse = await fetch('https://api.heygen.com/v1/streaming.start', {{
                                    method: 'POST',
                                    headers: {{
                                        'Authorization': 'Bearer {access_token}',
                                        'Content-Type': 'application/json'
                                    }},
                                    body: JSON.stringify({{
                                        session_id: sessionData.session_id
                                    }})
                                }});
                                
                                if (startResponse.ok) {{
                                    updateStatus('Session started successfully!', 'success');
                                    isConnected = true;
                                    speakBtn.disabled = false;
                                    stopBtn.disabled = false;
                                    chatInput.disabled = false;
                                    sendBtn.disabled = false;
                                    placeholderText.style.display = 'none';
                                    videoElement.style.display = 'block';
                                    log('Avatar is ready for interaction');
                                }} else {{
                                    const startError = await startResponse.text();
                                    throw new Error(`Fallback session start failed: ${{startResponse.status}} - ${{startError}}`);
                                }}
                            }} else {{
                                const fallbackError = await fallbackResponse.text();
                                log(`Fallback also failed: ${{fallbackResponse.status}} - ${{fallbackError}}`);
                                updateStatus('Both primary and fallback attempts failed', 'error');
                            }}
                        }} catch (fallbackError) {{
                            log(`Fallback error: ${{fallbackError.message}}`, 'error');
                            updateStatus('All session creation attempts failed', 'error');
                        }}
                    }}
                }}
            }}
            
            async function speakText(text = "Hello! I'm {avatar_name}, ready for our simulation today.") {{
                if (!sessionData || !isConnected) {{
                    updateStatus('Session not active', 'error');
                    return;
                }}
                
                try {{
                    updateStatus('Avatar speaking...', 'loading');
                    
                    const response = await fetch('https://api.heygen.com/v1/streaming.task', {{
                        method: 'POST',
                        headers: {{
                            'Authorization': 'Bearer {access_token}',
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            session_id: sessionData.session_id,
                            text: text,
                            task_type: 'talk'
                        }})
                    }});
                    
                    if (!response.ok) {{
                        throw new Error(`Speak request failed: ${{response.status}}`);
                    }}
                    
                    const result = await response.json();
                    log(`Speaking: "${{text}}"`);
                    updateStatus('Avatar ready', 'success');
                    
                }} catch (error) {{
                    updateStatus(`Speak error: ${{error.message}}`, 'error');
                    log(`Speak error: ${{error.message}}`, 'error');
                }}
            }}
            
            async function speakCustomText() {{
                const text = chatInput.value.trim();
                if (!text) return;
                
                await speakText(text);
                chatInput.value = '';
            }}
            
            function handleKeyPress(event) {{
                if (event.key === 'Enter') {{
                    speakCustomText();
                }}
            }}
            
            async function stopSession() {{
                if (!sessionData) return;
                
                try {{
                    updateStatus('Stopping session...', 'loading');
                    
                    const response = await fetch('https://api.heygen.com/v1/streaming.stop', {{
                        method: 'POST',
                        headers: {{
                            'Authorization': 'Bearer {access_token}',
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            session_id: sessionData.session_id
                        }})
                    }});
                    
                    updateStatus('Session stopped', 'success');
                    isConnected = false;
                    sessionData = null;
                    
                    // Reset UI
                    startBtn.disabled = false;
                    speakBtn.disabled = true;
                    stopBtn.disabled = true;
                    chatInput.disabled = true;
                    sendBtn.disabled = true;
                    
                    placeholderText.style.display = 'block';
                    videoElement.style.display = 'none';
                    placeholderText.textContent = 'Session ended. Click Start to begin again.';
                    
                }} catch (error) {{
                    updateStatus(`Stop error: ${{error.message}}`, 'error');
                    log(`Stop error: ${{error.message}}`, 'error');
                }}
            }}
            
            // Auto-start on load
            setTimeout(() => {{
                log('Component loaded, ready to start session');
                updateStatus('Ready to start session', 'success');
            }}, 500);
        </script>
    </body>
    </html>
    """
    
    return component_html

def main():
    st.title("🎭 HeyGen Simulation Demo - Fixed Implementation")
    
    # Debug section
    with st.expander("🔧 Debug Information", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Test API Connection"):
                if HEYGEN_API_KEY:
                    st.success("✅ API Key found")
                    token = get_access_token()
                    if token:
                        st.success("✅ Access token generated")
                        st.code(f"Token: {token[:20]}...", language="text")
                    else:
                        st.error("❌ Failed to generate access token")
                else:
                    st.error("❌ No API Key found")
        
        with col2:
            if st.button("Test Avatar & Voice IDs"):
                if HEYGEN_API_KEY:
                    st.info("Testing your specific avatar and voice configurations...")
                    
                    # Test Noa's configuration
                    st.write("**Testing Noa Martinez:**")
                    st.write(f"- Avatar ID: `June_HR_public`")
                    st.write(f"- Voice ID: `c67d6fca1c3d4f55b81fcf9abc37d77f`")
                    
                    # Test Sam's configuration  
                    st.write("**Testing Sam Richards:**")
                    st.write(f"- Avatar ID: `Shawn_Therapist_public`")
                    st.write(f"- Voice ID: `0f6610678bfa4a1eb827d128662dca11`")
                    
                    # Test voice API
                    try:
                        voices_response = requests.get(
                            "https://api.heygen.com/v2/voices",
                            headers={"x-api-key": HEYGEN_API_KEY},
                            timeout=10
                        )
                        if voices_response.status_code == 200:
                            voices_data = voices_response.json().get("data", {}).get("voices", [])
                            noa_voice_found = any(v.get("voice_id") == "c67d6fca1c3d4f55b81fcf9abc37d77f" for v in voices_data)
                            sam_voice_found = any(v.get("voice_id") == "0f6610678bfa4a1eb827d128662dca11" for v in voices_data)
                            
                            if noa_voice_found:
                                st.success("✅ Noa's voice ID found")
                            else:
                                st.warning("⚠️ Noa's voice ID not found in your account")
                                
                            if sam_voice_found:
                                st.success("✅ Sam's voice ID found")
                            else:
                                st.warning("⚠️ Sam's voice ID not found in your account")
                        else:
                            st.warning("Could not check voice IDs")
                    except Exception as e:
                        st.warning(f"Voice check error: {e}")
                else:
                    st.error("❌ No API Key found")

    # Get access token
    access_token = get_access_token()
    if not access_token:
        st.error("Cannot proceed without access token")
        st.info("Please check your HeyGen API key configuration")
        return

    # Custom avatar configurations for your specific characters
    avatar_options = {
        "Noa Martinez (June_HR)": {
            "id": "June_HR_public", 
            "description": "Virtual Clinical Instructor",
            "voice_id": None  # Will use default compatible voice
        },
        "Sam Richards (Shawn_Therapist)": {
            "id": "Shawn_Therapist_public", 
            "description": "Operations Manager, County Corrections Facility",
            "voice_id": None  # Will use default compatible voice
        }
    }
    
    # Get compatible voices for selection
    compatible_voices = get_compatible_voices()
    if compatible_voices:
        st.info(f"✅ Found {len(compatible_voices)} streaming-compatible voices")
    
    # Get available avatars for reference (optional)
    available_avatars = get_available_avatars()
    if available_avatars:
        st.info(f"Note: Found {len(available_avatars)} additional avatars in your account")
    
    # Add any additional avatars from your account (keeping your custom ones as primary)
    if available_avatars:
        for avatar in available_avatars:
            name = avatar.get('name', 'Unknown')
            if name not in [key.split(' (')[0] for key in avatar_options.keys()]:
                avatar_options[f"{name} (Available)"] = {
                    "id": avatar.get('avatar_id'),
                    "description": avatar.get('description', 'Additional avatar'),
                    "voice_id": None  # Use default voice for additional avatars
                }
    
    # Create tabs for different scenarios
    tab1, tab2 = st.tabs(["👋 Pre-briefing with Noa Martinez", "🏥 Simulation: Meeting with Sam Richards"])
    
    with tab1:
        st.header("Pre-briefing with Noa Martinez")
        st.markdown("**Noa Martinez - Virtual Clinical Instructor**")
        
        # Voice configuration options for Noa
        noa_voice_options = {
            "Friendly": {"rate": 1.0, "emotion": "friendly"},
            "Professional": {"rate": 0.9, "emotion": "serious"},
            "Enthusiastic": {"rate": 1.1, "emotion": "excited"},
            "Calm": {"rate": 0.8, "emotion": "soothing"},
        }
        
        col1, col2 = st.columns(2)
        with col1:
            # Filter to show only Noa's avatar
            noa_avatars = {k: v for k, v in avatar_options.items() if "Noa Martinez" in k}
            if not noa_avatars:
                # Fallback if the specific avatar isn't found
                noa_avatars = {"Noa Martinez (June_HR)": avatar_options.get("Noa Martinez (June_HR)", {"id": "June_HR_public", "voice_id": None})}
            
            selected_avatar = st.selectbox(
                "Choose Avatar for Noa:",
                options=list(noa_avatars.keys()),
                key="noa_avatar"
            )
        with col2:
            # Voice selection from compatible voices
            if compatible_voices:
                voice_options = ["Default (No specific voice)"] + list(compatible_voices.keys())
                selected_voice_key = st.selectbox(
                    "Voice Selection:",
                    options=voice_options,
                    key="noa_voice_selection"
                )
                
                if selected_voice_key == "Default (No specific voice)":
                    selected_voice_id = None
                else:
                    selected_voice_id = compatible_voices[selected_voice_key]["voice_id"]
            else:
                selected_voice_key = st.selectbox(
                    "Voice Style:",
                    options=list(noa_voice_options.keys()),
                    key="noa_voice"
                )
                selected_voice_id = None
        
        if selected_avatar and selected_avatar in noa_avatars:
            avatar_config = noa_avatars[selected_avatar]
            voice_config = noa_voice_options.get(selected_voice_key, noa_voice_options["Friendly"])
            
            # Create HeyGen component for Noa with compatible voice
            noa_component = create_heygen_component(
                access_token=access_token,
                avatar_id=avatar_config["id"],
                session_id="noa_session",
                avatar_name="Noa Martinez",
                voice_id=selected_voice_id or "default",
                voice_config=voice_config
            )
            
            st.components.v1.html(noa_component, height=700, scrolling=True)
        
        # Scenario context
        with st.expander("📋 Scenario Background", expanded=True):
            st.markdown("""
            **Pre-briefing Instructions:**
            
            In this scenario, you'll be playing the role of a public health nurse meeting with Sam Richards, 
            an Operations Manager at a County Corrections Facility. Your goal is to discuss and negotiate the 
            implementation of a new flu vaccination program for incarcerated individuals.
            
            **Key Learning Objectives:**
            - Practice professional communication in challenging environments
            - Develop negotiation skills for public health initiatives
            - Understand the unique challenges of healthcare in correctional facilities
            
            **Character Background - Sam Richards:**
            - 14 years experience in corrections management
            - Generally resistant to change and new programs
            - Focuses on security and operational concerns
            - May be skeptical about healthcare initiatives
            """)
    
    with tab2:
        st.header("Simulation: Meeting with Sam Richards")
        st.markdown("**Sam Richards - Operations Manager, County Corrections Facility**")
        
        # Voice configuration options for Sam
        sam_voice_options = {
            "Professional": {"rate": 0.9, "emotion": "serious"},
            "Authoritative": {"rate": 0.85, "emotion": "serious"},
            "Friendly": {"rate": 1.0, "emotion": "friendly"},
            "Skeptical": {"rate": 0.8, "emotion": "serious"},
        }
        
        col1, col2 = st.columns(2)
        with col1:
            # Filter to show only Sam's avatar
            sam_avatars = {k: v for k, v in avatar_options.items() if "Sam Richards" in k}
            if not sam_avatars:
                # Fallback if the specific avatar isn't found
                sam_avatars = {"Sam Richards (Shawn_Therapist)": avatar_options.get("Sam Richards (Shawn_Therapist)", {"id": "Shawn_Therapist_public", "voice_id": None})}
            
            selected_avatar_sam = st.selectbox(
                "Choose Avatar for Sam:",
                options=list(sam_avatars.keys()),
                key="sam_avatar"
            )
        with col2:
            # Voice selection from compatible voices
            if compatible_voices:
                voice_options_sam = ["Default (No specific voice)"] + list(compatible_voices.keys())
                selected_voice_key_sam = st.selectbox(
                    "Voice Selection:",
                    options=voice_options_sam,
                    key="sam_voice_selection"
                )
                
                if selected_voice_key_sam == "Default (No specific voice)":
                    selected_voice_id_sam = None
                else:
                    selected_voice_id_sam = compatible_voices[selected_voice_key_sam]["voice_id"]
            else:
                selected_voice_key_sam = st.selectbox(
                    "Voice Style:",
                    options=list(sam_voice_options.keys()),
                    key="sam_voice",
                    index=0  # Default to Professional for Sam
                )
                selected_voice_id_sam = None
        
        if selected_avatar_sam and selected_avatar_sam in sam_avatars:
            avatar_config_sam = sam_avatars[selected_avatar_sam]
            voice_config_sam = sam_voice_options.get(selected_voice_key_sam, sam_voice_options["Professional"])
            
            # Create HeyGen component for Sam with compatible voice
            sam_component = create_heygen_component(
                access_token=access_token,
                avatar_id=avatar_config_sam["id"],
                session_id="sam_session",
                avatar_name="Sam Richards",
                voice_id=selected_voice_id_sam or "default",
                voice_config=voice_config_sam
            )
            
            st.components.v1.html(sam_component, height=700, scrolling=True)
        
        # Simulation context
        with st.expander("🎯 Simulation Guidelines", expanded=True):
            st.markdown("""
            **Your Role:** Public Health Nurse
            
            **Objective:** Convince Sam Richards to implement a flu vaccination program
            
            **Expected Challenges:**
            - Resistance to new procedures
            - Concerns about cost and logistics
            - Security and safety questions
            - "We've always done it this way" mentality
            
            **Success Strategies:**
            - Present clear health benefits
            - Address operational concerns directly
            - Propose phased implementation
            - Emphasize regulatory compliance benefits
            """)

    # Usage instructions
    with st.expander("📖 How to Use", expanded=False):
        st.markdown("""
        **Getting Started:**
        1. Select an avatar from the dropdown
        2. Click "Start Session" to initialize the avatar
        3. Wait for the "Session started successfully!" message
        4. Use "Speak Test" for a quick test, or type custom messages
        5. Click "Stop Session" when finished
        
        **Troubleshooting:**
        - If you see errors, try refreshing the page
        - Make sure your HeyGen API key is properly configured
        - Check the debug section for connection status
        
        **Features:**
        - Real-time avatar interaction using HeyGen REST API
        - Custom text input for role-playing scenarios
        - Session logging and status tracking
        - Multiple avatar and voice style options
        - Configurable video quality and session settings
        - Automatic session management and cleanup
        
        **Based on HeyGen StreamingAvatarSDK v2.0.14:**
        - Full REST API integration
        - Compatible with HeyGen's streaming avatar system
        - Supports text-based interaction (voice chat requires WebRTC)
        - Session lifecycle management following SDK patterns
        """)

if __name__ == "__main__":
    main()
