"""
session.py  —  Singleton that carries login state across all modules.
Extended with:
  • current_role  ('Super' | 'Teacher')
  • admin_id      (int)
  • is_super / is_teacher  properties
  • clear()       wipes everything on logout
"""


class Session:
    _instance = None

    # ── state ──────────────────────────────────────────────────────────
    is_logged_in  = False
    current_user  = None          # username string
    current_role  = None          # 'Super' | 'Teacher'
    admin_id      = None          # int
    login_message = ""            # shown on the login screen after redirect

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ── helpers ────────────────────────────────────────────────────────
    @property
    def is_super(self):
        return self.current_role == "Super"

    @property
    def is_teacher(self):
        return self.current_role == "Teacher"

    def clear(self):
        """Wipe all session state on logout."""
        self.is_logged_in = False
        self.current_user = None
        self.current_role = None
        self.admin_id     = None


user_session = Session()
