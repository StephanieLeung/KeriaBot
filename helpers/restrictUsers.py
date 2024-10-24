class RestrictedUser:
    _instance = None  # Singleton instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RestrictedUser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'users'):  # Avoid re-initializing if already initialized
            self.users = []

    def add_user(self, user):
        self.users.append(user)

    def remove_user(self, user):
        try:
            self.users.remove(user)
        except ValueError:
            return

    def is_restricted(self, user):
        return user in self.users


restricted_users = RestrictedUser()