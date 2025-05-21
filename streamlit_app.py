import streamlit as st
import requests
import json
import time
import re
import streamlit.components.v1 as components
from typing import Dict, List, Optional, Union

# Set page configuration
st.set_page_config(
    page_title="Clinical Simulation with Virtual Avatars",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define constants
HEYGEN_API_URL = "https://api.heygen.com"

# Simulation stages
STAGE_INTRO = "intro"
STAGE_PREBRIEF = "prebrief"
STAGE_SIMULATION = "simulation"
STAGE_DEBRIEF = "debrief"
STAGE_END = "end"

# Character definitions
CHARACTER_NOA = "noa"
CHARACTER_SAM = "sam"

# Default avatar and voice IDs
AVATAR_CONFIG = {
    CHARACTER_NOA: {
        "avatar_id": "June_HR_public",
        "voice_id": "c67d6fca1c3d4f55b81fcf9abc37d77f",
        "name": "Noa Martinez",
        "role": "Virtual Clinical Instructor"
    },
    CHARACTER_SAM: {
        "avatar_id": "Shawn_Therapist_public",
        "voice_id": "0f6610678bfa4a1eb827d128662dca11",
        "name": "Sam Richards",
        "role": "Operations Manager, County Corrections Facility"
    }
}

# Initialize session state variables if they don't exist
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "stage" not in st.session_state:
    st.session_state.stage = STAGE_INTRO
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "active_character" not in st.session_state:
    st.session_state.active_character = CHARACTER_NOA
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "simulation_responses" not in st.session_state:
    st.session_state.simulation_responses = 0
if "simulation_progress" not in st.session_state:
    st.session_state.simulation_progress = 0

# Helper functions for API interactions
def get_access_token(api_key: str) -> Union[str, None]:
    """Get access token from HeyGen API."""
    try:
        response = requests.post(
            f"{HEYGEN_API_URL}/v1/streaming.create_token",
            headers={"X-Api-Key": api_key}
        )
        data = response.json()
        if response.status_code == 200 and "data" in data and "token" in data["data"]:
            return data["data"]["token"]
        else:
            st.error(f"Failed to get access token: {data.get('error', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error getting access token: {str(e)}")
        return None

# Load character script responses
def load_sam_responses():
    """Load the character responses for Sam."""
    # These are simplified response sets based on the script provided
    return {
        "opening": [
            "Yeah, I got the memo about this meeting. Listen, we're already stretched thin here. Another program from county health? We just got through that mental health screening thing last year and that was a nightmare for our scheduling.",
            "Alright, let's get this over with. I've got a facility to run, and this 'vaccine program' is just another headache. What exactly are you asking us to do?",
            "Look, I don't have a lot of time, so let's get to it. You want to talk about this flu shot program, right? I'm not sure why we even need it. Our facility has been running just fine without it."
        ],
        "security": [
            "Do you have any idea what it takes to move inmates around this facility? Every time we transport someone, that's a security risk. Now you want us to coordinate moving hundreds of inmates for shots? Who's going to handle that security? Not your people, that's for sure.",
            "Security is my top priority. Every movement in this facility is a potential incident. Your team coming in here with medical equipment, syringes... that's a security risk I'm not sure we can manage with our current staffing."
        ],
        "staffing": [
            "We're already short-staffed. Three officers called in sick just today. Who's going to supervise all this? We can't spare the manpower to watch over your health team while they give shots.",
            "Hold on. You think we have the staff for this? My officers are already stretched thin with lockdowns and inmate movements. Where's the extra manpower coming from? And don't say 'reprioritize'—we're at capacity."
        ],
        "space": [
            "Where exactly do you think this is going to happen? Our medical area has two exam rooms. TWO. And they're booked solid with urgent care issues. We don't have space for a vaccination clinic.",
            "Phased? So we disrupt routines indefinitely? Inmates thrive on predictability. Even minor changes cause unrest. Last month, a shift in meal times led to a riot. Tell me, Nurse—how many correctional facilities have you managed?"
        ],
        "paperwork": [
            "So who's handling all the paperwork for this? My staff isn't trained on medical documentation. And if something goes wrong with one of these vaccines, who's liable? Us or you? These questions matter in corrections.",
            "Paperwork alone will bury us. Every shot needs consent forms, logs, incident reports. Our admin team is drowning in OSHA audits. Who's handling the extra load? You?"
        ],
        "budget": [
            "Nobody told me about any budget for this. Who's paying for the extra officer hours? The cleanup? The extra administrative work? Our budget was finalized months ago.",
            "Money's always tight, but I don't see how spending more upfront saves us anything. Besides, sick inmates just stay in their cells—problem solved."
        ],
        "resistance": [
            "You know most of these inmates don't want these vaccines, right? We'll have refusals left and right. Some of them think the government is trying to experiment on them. Then what? Force them? That's a lawsuit waiting to happen.",
            "Education? These aren't kindergarteners. Inmates don't trust us, and they'll think this is some experiment. And if you offer 'incentives' like extra rec time, the gangs will exploit it. Security risks skyrocket—you ready to take responsibility for that?"
        ],
        "schedule": [
            "Our facility runs on a tight schedule. Meals, yard time, visits, work duties - it's all carefully coordinated. Your vaccination program throws all that into chaos.",
            "Staggered schedules? You ever tried coordinating 500 inmates during flu season? They'll refuse just to cause delays. Last time we rolled out TB testing, half the block staged a hunger strike. What's your plan for that?"
        ],
        "past_failures": [
            "Last year, county mental health came in with their new screening program. Took twice as long as they said it would. Left us with a backlog of intake processing that took months to clear. Why would this be any different?",
            "Look, they're incarcerated for a reason. They gave up certain luxuries. Nobody said jail was supposed to be comfortable. Flu shots sound like a privilege, not a necessity."
        ],
        "evidence": [
            "That might work in theory or in some other facility, but you don't understand how things work HERE. Our situation is different.",
            "Data? Every facility's different. Our population has more comorbidities. What if vaccines cause adverse reactions here? Our infirmary can't handle a surge. Did your 'data' account for that?"
        ],
        "alternatives": [
            "Look, if you want my honest opinion, just leave the vaccines with our medical staff and let them give them during regular sick call. No special program needed. That's how we've always handled it.",
            "A trial? You mean a foot in the door for you to roll this thing out full-scale later? I've seen this play before. First, it's optional, then it's 'strongly recommended,' and before you know it, we're forced to do it."
        ],
        "closing": [
            "I'll have to take this up with the warden. Don't expect a quick decision. We've got real security issues to deal with around here. I'll be in touch... eventually.",
            "I just don't see how this works without creating a mess for us. Maybe someone higher up will force it through, but I wouldn't count on me making this easy for you. If you want to keep pushing, take it up with my boss."
        ],
        "fallback": [
            "Look, that sounds nice on paper, but in reality, it's never that simple in a corrections facility.",
            "I've been doing this for 14 years. Trust me, these kinds of programs always end up causing more problems than they solve.",
            "We've heard all this before from other programs. Always big promises, never enough support.",
            "That's not how things work around here. We have protocols and security concerns that come first.",
            "I'm not convinced this is worth the disruption it's going to cause to our operations."
        ]
    }

def get_sam_response(context: str) -> str:
    """Get an appropriate response from Sam based on the context."""
    responses = load_sam_responses()
    
    # Map keywords to response categories
    keywords = {
        r'\b(hi|hello|introduce|introduction|start)\b': "opening",
        r'\b(secur|safe|guard|risk|danger)\b': "security",
        r'\b(staff|officer|personnel|manpower|short-staffed)\b': "staffing",
        r'\b(space|room|area|facility|place)\b': "space",
        r'\b(document|paperwork|form|liability|responsible)\b': "paperwork",
        r'\b(budget|cost|fund|money|expense|pay)\b': "budget",
        r'\b(inmate|refus|consent|resist|willing|voluntary)\b': "resistance",
        r'\b(schedule|time|disrupt|routine|coordination)\b': "schedule",
        r'\b(previous|before|last|history|past|failed)\b': "past_failures",
        r'\b(evidence|data|research|study|statistic|show|prove)\b': "evidence",
        r'\b(alternative|option|suggestion|recommend|instead)\b': "alternatives",
        r'\b(end|finish|conclude|next step|follow|warden)\b': "closing",
    }
    
    # Find matching category based on keywords
    category = None
    for pattern, cat in keywords.items():
        if re.search(pattern, context.lower()):
            category = cat
            break
    
    # If no category matched, use the fallback
    if category is None or category not in responses:
        category = "fallback"
    
    # Get a response from the category
    response_list = responses[category]
    response_index = st.session_state.simulation_responses % len(response_list)
    st.session_state.simulation_responses += 1
    
    return response_list[response_index]

def add_to_conversation(character: str, text: str):
    """Add a message to the conversation history."""
    st.session_state.conversation_history.append({
        "character": character,
        "text": text,
        "timestamp": time.time()
    })

def display_conversation_history():
    """Display the conversation history."""
    if st.session_state.conversation_history:
        st.markdown("### Conversation History")
        for entry in st.session_state.conversation_history:
            if entry["character"] == CHARACTER_NOA:
                st.markdown(f"**Noa**: {entry['text']}")
            elif entry["character"] == CHARACTER_SAM:
                st.markdown(f"**Sam**: {entry['text']}")
            else:  # Student
                st.markdown(f"**You**: {entry['text']}")

# HeyGen Avatar Component using JavaScript SDK
def heygen_avatar_component(access_token, avatar_id, voice_id, height=500, character="noa"):
    """Create a HeyGen Avatar component using the JavaScript SDK."""
    
    # Create a unique div id for this avatar instance
    div_id = f"avatar-container-{character}"
    
    # JavaScript for initializing the avatar - Fixed version with more debugging
    component_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HeyGen Avatar</title>
        <style>
            #container {{
                width: 100%;
                height: {height}px;
                background-color: #000;
                position: relative;
                border-radius: 8px;
                overflow: hidden;
            }}
            #status {{
                position: absolute;
                bottom: 10px;
                left: 10px;
                background-color: rgba(0, 0, 0, 0.6);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                font-family: sans-serif;
            }}
            #error {{
                color: red;
                margin: 10px;
                font-family: sans-serif;
            }}
        </style>
    </head>
    <body>
        <div id="container">
            <div id="status">Loading SDK...</div>
        </div>
        <div id="error"></div>
        
        <script>
            const errorDiv = document.getElementById('error');
            const statusDiv = document.getElementById('status');
            
            // Debug info
            console.log("Starting initialization for {character} avatar");
            statusDiv.innerText = "Loading SDK...";
            
            // First, load the SDK from CDN
            function loadScript(url) {{
                return new Promise((resolve, reject) => {{
                    const script = document.createElement('script');
                    script.src = url;
                    script.async = true;
                    script.onload = resolve;
                    script.onerror = reject;
                    document.body.appendChild(script);
                }});
            }}
            
            // Initialize the avatar
            async function initializeAvatar() {{
                try {{
                    await loadScript('https://cdn.jsdelivr.net/npm/@heygen/streaming-avatar@2.0.14/dist/index.umd.js');
                    statusDiv.innerText = "SDK loaded, initializing avatar...";
                    console.log("SDK loaded for {character}");
                    
                    // Verify SDK is loaded
                    if (typeof StreamingAvatar === 'undefined') {{
                        throw new Error("StreamingAvatar is not defined after loading script");
                    }}
                    
                    // Create the streaming avatar instance
                    const avatar = new StreamingAvatar({{
                        token: "{access_token}"
                    }});
                    
                    window.avatar_{character} = avatar;
                    console.log("Avatar instance created");
                    
                    // Set up event listeners
                    avatar.on("STREAM_READY", (event) => {{
                        console.log("Stream ready event:", event);
                        statusDiv.innerText = "Connected";
                    }});
                    
                    avatar.on("STREAM_DISCONNECTED", () => {{
                        console.log("Stream disconnected");
                        statusDiv.innerText = "Disconnected";
                    }});
                    
                    avatar.on("AVATAR_START_TALKING", () => {{
                        console.log("Avatar started talking");
                        statusDiv.innerText = "Speaking...";
                    }});
                    
                    avatar.on("AVATAR_STOP_TALKING", () => {{
                        console.log("Avatar stopped talking");
                        statusDiv.innerText = "Connected";
                    }});
                    
                    // Create and start the avatar session
                    statusDiv.innerText = "Creating avatar session...";
                    console.log("Starting avatar creation with:", {{
                        quality: "Medium",
                        avatarName: "{avatar_id}",
                        voice: {{ voiceId: "{voice_id}" }}
                    }});
                    
                    const sessionInfo = await avatar.createStartAvatar({{
                        quality: "Medium",
                        avatarName: "{avatar_id}",
                        voice: {{
                            voiceId: "{voice_id}"
                        }}
                    }});
                    
                    console.log("Session created:", sessionInfo);
                    statusDiv.innerText = "Avatar ready";
                    
                    // Create global function to speak
                    window.speakText_{character} = function(text) {{
                        console.log("Speaking:", text);
                        avatar.speak({{ text: text, task_type: "REPEAT" }});
                    }};
                    
                    // Try a test message
                    setTimeout(() => {{
                        console.log("Testing avatar with greeting");
                        avatar.speak({{ text: "Hello", task_type: "REPEAT" }});
                    }}, 3000);
                    
                }} catch (error) {{
                    console.error("Error initializing avatar:", error);
                    errorDiv.innerText = "Error: " + error.message;
                    statusDiv.innerText = "Initialization failed";
                }}
            }}
            
            // Start initialization
            initializeAvatar();
        </script>
    </body>
    </html>
    """
    
    # Render the HTML component
    components.html(component_html, height=height + 50)
    
    return True

# Define prebriefing text ahead of time so it's available in scope
PREBRIEF_TEXT = """
Hello, I'm Noa Martinez, your Virtual Clinical Instructor for today's simulation. 

In this scenario, you'll be playing the role of a public health nurse meeting with Sam Richards, 
an Operations Manager at a County Corrections Facility. Your goal is to discuss and negotiate 
the implementation of a new flu vaccination program for incarcerated individuals.

Sam has been in his position for 14 years and tends to be resistant to change. He's defensive 
of current processes and often focuses on problems rather than solutions. His communication style 
can be challenging - he may interrupt you, use dismissive language, and rely on "we've always 
done it this way" reasoning.

Your objectives are to:
1. Build rapport despite resistance
2. Address concerns constructively
3. Use data effectively to support your case
4. Navigate the power dynamics
5. Apply change management principles

Remember to maintain your professionalism even when faced with resistance. Take notes on Sam's 
objections so we can discuss them in the debriefing.

Are you ready to begin the simulation?
"""

TRANSITION_TEXT = """
Great! Remember your objectives and stay focused on your goal of implementing the 
flu vaccination program. I'll be observing and we'll discuss your interaction afterwards. 
Good luck with Sam!
"""

DEBRIEF_TEXT = """
Great job completing the simulation! Let's take some time to reflect on your interaction with Sam.

I noticed that Sam presented several barriers to implementing the flu vaccination program. 
Let's discuss how you addressed these objections and what strategies were effective.

What aspects of the interaction did you find most challenging? What approaches worked well 
for you in addressing Sam's resistance?
"""

# UI elements and workflow functions
def display_intro_page():
    """Display the introduction page."""
    st.title("Clinical Simulation with Virtual Avatars")
    
    st.markdown("""
    ## Welcome to the Virtual Simulation Environment
    
    This application simulates a clinical scenario where you (as a public health nurse) 
    will interact with Sam Richards, an Operations Manager at a County Corrections Facility,
    to discuss implementing a new flu vaccination program.
    
    Your virtual clinical instructor, Noa Martinez, will guide you through the process.
    
    ### Simulation Flow:
    1. **Pre-briefing**: Noa will explain the scenario and your objectives
    2. **Simulation**: You'll interact with Sam Richards to negotiate the implementation
    3. **Debriefing**: Noa will help you reflect on the experience
    
    ### Getting Started
    Please enter your HeyGen API key to begin the simulation.
    """)
    
    # Try to load API key from secrets first
    try:
        api_key = st.secrets["heygen_api_key"]
        st.session_state.api_key = api_key
        st.success("API key loaded from Streamlit secrets")
    except:
        # If not available, show input field
        api_key = st.text_input("HeyGen API Key", type="password", key="api_key_input")
        st.session_state.api_key = api_key
    
    if st.button("Start Simulation"):
        if st.session_state.api_key:
            # Get access token
            access_token = get_access_token(st.session_state.api_key)
            if access_token:
                st.session_state.access_token = access_token
                st.session_state.stage = STAGE_PREBRIEF
                st.rerun()
            else:
                st.error("Failed to get access token. Please check your API key.")
        else:
            st.warning("Please enter your HeyGen API key to proceed.")

def display_prebrief_page():
    """Display the pre-briefing page."""
    st.title("Pre-briefing with Noa Martinez")
    
    # Create two columns - one for avatar and one for conversation
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display the Noa avatar using the JavaScript SDK
        if st.session_state.access_token:
            heygen_avatar_component(
                st.session_state.access_token,
                AVATAR_CONFIG[CHARACTER_NOA]["avatar_id"],
                AVATAR_CONFIG[CHARACTER_NOA]["voice_id"],
                height=400,
                character=CHARACTER_NOA
            )
    
    with col2:
        st.markdown(f"### {AVATAR_CONFIG[CHARACTER_NOA]['name']} - {AVATAR_CONFIG[CHARACTER_NOA]['role']}")
        
        # Pre-briefing script
        if not st.session_state.conversation_history:
            # Add to conversation history
            add_to_conversation(CHARACTER_NOA, PREBRIEF_TEXT)
    
    # JavaScript to speak through the avatar
    if st.session_state.conversation_history and len(st.session_state.conversation_history) == 1:
        # Run JavaScript to make the avatar speak - using a simple approach without referring to an undefined variable
        components.html(
            """
            <script>
                function attemptToSpeak() {
                    if (window.avatar_noa) {
                        window.avatar_noa.speak({ 
                            text: "Hello, I'm Noa Martinez, your Virtual Clinical Instructor for today's simulation.", 
                            task_type: "REPEAT" 
                        });
                        return true;
                    }
                    return false;
                }
                
                // Try multiple times in case the avatar isn't ready yet
                let attempts = 0;
                let maxAttempts = 10;
                let success = false;
                
                function trySpeak() {
                    if (attempts >= maxAttempts || success) return;
                    
                    success = attemptToSpeak();
                    if (!success) {
                        attempts++;
                        setTimeout(trySpeak, 1000);
                    }
                }
                
                // Start trying after a delay
                setTimeout(trySpeak, 3000);
            </script>
            """,
            height=0
        )
    
    # Display conversation history
    display_conversation_history()
    
    # User input
    user_message = st.text_input("Your response:", key="user_input_prebrief")
    
    if st.button("Send", key="send_prebrief"):
        if user_message:
            # Add user message to conversation
            add_to_conversation("student", user_message)
            
            # Generate a response from Noa
            noa_response = "I understand. Remember that your goal is to advocate for the implementation of the flu vaccination program while addressing Sam's concerns."
            add_to_conversation(CHARACTER_NOA, noa_response)
            
            # Clear the input
            st.session_state.user_input_prebrief = ""
            
            st.rerun()
    
    # Button to start simulation
    if st.button("Start Simulation"):
        # Final instruction before simulation
        add_to_conversation(CHARACTER_NOA, TRANSITION_TEXT)
        
        # Switch to simulation stage
        st.session_state.stage = STAGE_SIMULATION
        st.rerun()

def display_simulation_page():
    """Display the simulation page."""
    st.title("Simulation: Meeting with Sam Richards")
    
    # Create two columns - one for avatar and one for conversation
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display the Sam avatar using the JavaScript SDK
        if st.session_state.access_token:
            heygen_avatar_component(
                st.session_state.access_token,
                AVATAR_CONFIG[CHARACTER_SAM]["avatar_id"],
                AVATAR_CONFIG[CHARACTER_SAM]["voice_id"],
                height=400,
                character=CHARACTER_SAM
            )
    
    with col2:
        st.markdown(f"### {AVATAR_CONFIG[CHARACTER_SAM]['name']} - {AVATAR_CONFIG[CHARACTER_SAM]['role']}")
        
        # Initial greeting from Sam if this is the start of the simulation
        if not any(entry["character"] == CHARACTER_SAM for entry in st.session_state.conversation_history):
            opening_lines = load_sam_responses()["opening"]
            opening_line = opening_lines[0]  # Use the first opening line
            add_to_conversation(CHARACTER_SAM, opening_line)
    
    # Display conversation history
    display_conversation_history()
    
    # User input
    user_message = st.text_input("Your response:", key="user_input_simulation")
    
    if st.button("Send", key="send_simulation"):
        if user_message:
            # Add user message to conversation
            add_to_conversation("student", user_message)
            
            # Get Sam's response based on the context
            sam_response = get_sam_response(user_message)
            add_to_conversation(CHARACTER_SAM, sam_response)
            
            # Progress the simulation
            st.session_state.simulation_progress += 1
            
            # Clear the input
            st.session_state.user_input_simulation = ""
            
            # After 5 exchanges, move to debrief
            if st.session_state.simulation_progress >= 5:
                # One final response from Sam before ending
                closing_response = "I'll have to take this up with the warden. Don't expect a quick decision. We've got real security issues to deal with around here. I'll be in touch... eventually."
                add_to_conversation(CHARACTER_SAM, closing_response)
                
                # Switch back to Noa for debriefing
                st.session_state.stage = STAGE_DEBRIEF
            
            st.rerun()
    
    # Allow manually ending the simulation
    if st.button("End Simulation"):
        st.session_state.stage = STAGE_DEBRIEF
        st.rerun()

def display_debrief_page():
    """Display the debriefing page."""
    st.title("Debriefing with Noa Martinez")
    
    # Create two columns - one for avatar and one for conversation
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display the Noa avatar using the JavaScript SDK
        if st.session_state.access_token:
            heygen_avatar_component(
                st.session_state.access_token,
                AVATAR_CONFIG[CHARACTER_NOA]["avatar_id"],
                AVATAR_CONFIG[CHARACTER_NOA]["voice_id"],
                height=400,
                character=CHARACTER_NOA
            )
    
    with col2:
        st.markdown(f"### {AVATAR_CONFIG[CHARACTER_NOA]['name']} - {AVATAR_CONFIG[CHARACTER_NOA]['role']}")
        
        # Initial debrief from Noa if this is the start of the debriefing
        if not any(entry["character"] == CHARACTER_NOA and "Great job" in entry["text"] for entry in st.session_state.conversation_history):
            add_to_conversation(CHARACTER_NOA, DEBRIEF_TEXT)
    
    # Display conversation history
    display_conversation_history()
    
    # User input
    user_message = st.text_input("Your response:", key="user_input_debrief")
    
    if st.button("Send", key="send_debrief"):
        if user_message:
            # Add user message to conversation
            add_to_conversation("student", user_message)
            
            # Generate a response from Noa
            noa_response = "Thank you for sharing your reflections. It's important to analyze these interactions to grow as a healthcare professional. What other insights did you gain from this experience?"
            add_to_conversation(CHARACTER_NOA, noa_response)
            
            # Clear the input
            st.session_state.user_input_debrief = ""
            
            st.rerun()
    
    # Button to end session
    if st.button("Complete Simulation"):
        st.session_state.stage = STAGE_END
        st.rerun()

def display_end_page():
    """Display the end page."""
    st.title("Simulation Complete")
    
    st.markdown("""
    ## Thank you for completing the simulation!
    
    We hope this experience has helped you develop skills in:
    
    - Communicating with resistant stakeholders
    - Applying change management principles
    - Advocating for public health initiatives
    - Navigating organizational dynamics
    
    Your conversation history has been recorded for your reference.
    """)
    
    # Display conversation history
    display_conversation_history()
    
    # Button to restart
    if st.button("Start New Simulation"):
        # Reset session state
        for key in list(st.session_state.keys()):
            if key != "api_key" and key != "access_token":
                del st.session_state[key]
        
        # Initialize new session
        st.session_state.stage = STAGE_INTRO
        st.session_state.conversation_history = []
        st.session_state.simulation_responses = 0
        st.session_state.simulation_progress = 0
        
        st.rerun()

# Main application flow
def main():
    # Try to load API key from secrets
    if not st.session_state.api_key:
        try:
            st.session_state.api_key = st.secrets["heygen_api_key"]
        except:
            # Will use the input field instead
            pass
    
    # Try to get access token if we have API key but no token
    if st.session_state.api_key and not st.session_state.access_token:
        st.session_state.access_token = get_access_token(st.session_state.api_key)
    
    # Display appropriate page based on current stage
    if st.session_state.stage == STAGE_INTRO:
        display_intro_page()
    elif st.session_state.stage == STAGE_PREBRIEF:
        display_prebrief_page()
    elif st.session_state.stage == STAGE_SIMULATION:
        display_simulation_page()
    elif st.session_state.stage == STAGE_DEBRIEF:
        display_debrief_page()
    elif st.session_state.stage == STAGE_END:
        display_end_page()
    else:
        st.error("Unknown stage. Resetting to intro.")
        st.session_state.stage = STAGE_INTRO
        st.rerun()

if __name__ == "__main__":
    main()
