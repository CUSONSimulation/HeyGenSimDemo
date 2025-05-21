# Clinical Simulation with HeyGen Interactive Avatars

This Streamlit application creates an interactive clinical simulation using HeyGen's streaming avatar technology. It simulates a scenario where a public health nurse (the student) interacts with a corrections middle manager (Sam Richards) about implementing a flu vaccination program, with guidance from a virtual clinical instructor (Noa Martinez).

## Features

- Interactive avatars powered by HeyGen's streaming technology
- Complete simulation workflow: pre-briefing, simulation, and debriefing
- Character-driven responses based on simulation script
- Client-side integration with HeyGen's JavaScript SDK
- Session state management for smooth simulation flow

## Technical Implementation

This application uses:
- HeyGen's JavaScript SDK (`@heygen/streaming-avatar`) for avatar integration
- Streamlit Components for client-side JavaScript execution
- WebRTC technology for streaming avatars
- Streamlit session state for simulation state management

## Installation

1. Clone this repository:
```bash
git clone https://github.com/your-username/clinical-simulation.git
cd clinical-simulation
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Set up your HeyGen API key:
   - Create a `.streamlit/secrets.toml` file with the following content:
     ```toml
     heygen_api_key = "your-api-key-here"
     ```
   - Alternatively, you can input your API key directly in the application

## Usage

1. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. Follow the on-screen instructions to:
   - Enter your HeyGen API key (if not in secrets)
   - Go through pre-briefing with the virtual instructor (Noa)
   - Conduct the simulation conversation with Sam
   - Participate in the debriefing to reflect on the experience

## Avatar and Voice Configuration

The application is configured to use the following HeyGen avatars and voices:

- **Noa Martinez (Virtual Clinical Instructor)**
  - Avatar ID: June_HR_public
  - Voice ID: c67d6fca1c3d4f55b81fcf9abc37d77f

- **Sam Richards (Operations Manager)**
  - Avatar ID: Shawn_Therapist_public
  - Voice ID: 0f6610678bfa4a1eb827d128662dca11

## Browser Requirements

Since this application uses WebRTC technology for streaming avatars, it requires:
- A modern web browser (Chrome, Firefox, or Edge recommended)
- JavaScript enabled
- WebRTC support
- No extreme firewall or proxy limitations

## Important Notes

- HeyGen's streaming avatar functionality has usage limits based on your subscription
- This application is designed for educational purposes in healthcare professional training
- For the best experience, use a device with a good internet connection

## Troubleshooting

If you encounter issues:
1. Check your HeyGen API key and subscription status
2. Ensure your browser supports WebRTC and has JavaScript enabled
3. Check your internet connection
4. Try clearing your browser cache
5. Make sure the avatar IDs are still available on your HeyGen account

## License

This project uses the HeyGen SDK, which is licensed under the MIT License. Please see the LICENSE file for details.

## Acknowledgments

- HeyGen for their streaming avatar technology
- Streamlit for the application framework
- Simulation script developed for educational purposes
