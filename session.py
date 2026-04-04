class Session:
    _instance = None
    is_logged_in = False
    current_user = None
    login_message = ""  # New: To show "Please login first"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Session, cls).__new__(cls)
        return cls._instance

user_session = Session()