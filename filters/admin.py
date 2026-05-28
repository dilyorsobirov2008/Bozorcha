# Admin authentication is handled via FSM states (AdminStates).
#
# The admin flow works as follows:
# 1. User navigates to admin panel from the main menu.
# 2. Bot transitions to AdminStates.entering_login and prompts for login.
# 3. After login, bot transitions to AdminStates.entering_password.
# 4. AdminService.authenticate() verifies credentials.
# 5. On success, FSM moves to AdminStates.in_admin_menu.
# 6. All admin handlers are gated by the AdminStates state group,
#    so unauthenticated users cannot access admin functionality.
#
# No separate aiogram filter is needed because FSM state matching
# already restricts access to admin-only handlers.
