from datetime import datetime

def get_current_time(args=None):
    """Function to get current time that will be called by the agent"""
    current_time = datetime.now()
    return {
        "time": current_time.strftime("%H:%M:%S"),
        "date": current_time.strftime("%Y-%m-%d")
    }
