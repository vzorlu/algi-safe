import os


class Config:
    API_KEY = os.environ.get("RETELL_API_KEY", "key_af612dbafebc643d7491e2a407fd")
    AGENT_ID = os.environ.get("RETELL_AGENT_ID", "agent_19a676d6a7174ae1204489cc12")
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev")
