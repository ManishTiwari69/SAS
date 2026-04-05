# validate.py
import re
from tkinter import messagebox

class Validator:

    @staticmethod
    def validate_all(data):
        errors = {}
        # Allows only English letters and spaces (no digits or symbols)
        alpha_pattern = r"^[a-zA-Z\s]+$"
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        pass_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$"

        for field, value in data.items():
            # Skip Middle Name if it's empty (it's optional)
            if field == "mname" and not str(value).strip():
                continue
            
            # 1. Required Check
            if not str(value).strip():
                errors[field] = "This field is required"
                continue

            # 2. No Digits/Symbols Check (Names & Relationship)
            if field in ["fname", "lname", "mname", "p_name", "p_rel"]:
                if not re.match(alpha_pattern, str(value)):
                    errors[field] = "Must contain only letters"

        # 3. Format Checks (only if not already marked empty)
        if 'email' not in errors and not re.match(email_pattern, data.get('email', '')):
            errors['email'] = "Invalid email format"
            
        if 'pass' not in errors and not re.match(pass_pattern, data.get('pass', '')):
            errors['pass'] = "8+ chars, Upper, Lower, Num, Symbol"
            
        for p_field in ['phone', 'p_phone']:
            if p_field not in errors:
                val = data.get(p_field, '')
                if not val.isdigit() or len(val) != 10:
                    errors[p_field] = "Must be 10 digits"

        return errors
    
    @staticmethod
    def is_empty(fields_dict):
        """Checks if any field in {Label: Value} is empty."""
        for label, value in fields_dict.items():
            if not str(value).strip():
                messagebox.showwarning("Input Error", f"'{label}' cannot be empty!")
                return True
        return False

    @staticmethod
    def is_valid_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            messagebox.showwarning("Input Error", "Please enter a valid email address.")
            return False
        return True

    @staticmethod
    def is_valid_phone(phone, label="Phone number"):
        if not phone.isdigit() or len(phone) != 10:
            messagebox.showwarning("Input Error", f"{label} must be exactly 10 digits.")
            return False
        return True

    @staticmethod
    def is_numeric(value, label="Field"):
        if not str(value).isdigit():
            messagebox.showwarning("Input Error", f"{label} must contain only numbers.")
            return False
        return True

    @staticmethod
    def is_strong_password(password):
        """Checks for length, upper, lower, digit, and special char."""
        if len(password) < 8:
            messagebox.showwarning("Security", "Password must be at least 8 characters long.")
            return False
            
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$"
        if not re.match(pattern, password):
            messagebox.showwarning("Security", 
                "Password is too weak!\n\n"
                "Must include:\n"
                "• Uppercase & Lowercase letters\n"
                "• At least one Number\n"
                "• At least one Special Character (!@#$%^&*)")
            return False
        return True

    @staticmethod
    def get_password_strength(password):
        """Returns (Color, Label) based on password complexity."""
        score = 0
        if not password: return ("#ffffff", "")
        
        if len(password) >= 8: score += 1
        if re.search(r"[A-Z]", password): score += 1
        if re.search(r"[a-z]", password): score += 1
        if re.search(r"[\d]", password): score += 1
        if re.search(r"[@$!%*?&#]", password): score += 1
        
        strength_map = {
            0: ("#e74c3c", "Too Short"),
            1: ("#e74c3c", "Weak"),
            2: ("#f1c40f", "Fair"),
            3: ("#3498db", "Good"),
            4: ("#2ecc71", "Strong"),
            5: ("#27ae60", "Very Strong")
        }
        return strength_map.get(score, ("#e74c3c", "Weak"))