1. Hardware Server (The Python Code)
This is the backend engine. It connects directly to your NooElec radio hardware to read actual satellite radio waves. It calculates the signal strength, packages it together with other simulated satellite data, and continuously broadcasts it over a web connection so the dashboard can read it in real time.

2. Visual Dashboard (The JavaScript Code)
This is the frontend user interface. It tells the Open MCT software how to display your satellite data. It sets up the folders in the menu, defines the specific measurements you are tracking (like signal strength, battery voltage, and altitude), and listens for a live stream of data coming from the Python server.
