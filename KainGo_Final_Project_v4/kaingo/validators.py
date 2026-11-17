"""Validation rules ported from manolo_real (Register_System)."""
import re

INVALID_NAMES = {"hello", "test", "admin", "unknown", "sample", "asdf", "asdfgh",
                 "qwerty", "qwertyuiop", "zxcvbn", "abc", "name"}
FAKE_EMAILS = {"admin", "test", "hello", "sample", "asdf", "qwerty", "gmail",
               "user", "unknown", "abc123", "12345"}
TOP_LEVEL = {"edu", "gov", "mil", "org", "int"}
SECOND_LEVEL = {"edu", "gov", "ac", "go", "sch", "org", "mil"}

# Real PH network prefixes (Globe, TM, Smart, TNT, Sun, DITO)
PREFIXES = set("""0905 0906 0915 0916 0917 0926 0927 0935 0936 0937 0945 0953 0954 0955
0956 0965 0966 0967 0975 0976 0977 0978 0979 0995 0996 0997 0907 0908 0909 0910 0911 0912
0913 0914 0918 0919 0920 0921 0922 0923 0924 0925 0928 0929 0930 0931 0932 0933 0934 0938
0939 0940 0941 0942 0943 0944 0946 0947 0948 0949 0950 0951 0961 0963 0968 0969 0970 0973
0974 0981 0989 0998 0999 0991 0992 0993 0994""".split())


def is_agency_domain(host):
    labels = host.lower().rstrip(".").split(".")
    if len(labels) < 2 or labels[0] == "":
        return False
    if labels[-1] in TOP_LEVEL:
        return True
    return len(labels) >= 3 and re.fullmatch(r"[a-z]{2}", labels[-1]) and labels[-2] in SECOND_LEVEL


def is_ph_mobile(number):
    if not re.fullmatch(r"09[0-9]{9}", number) or number[:4] not in PREFIXES:
        return False
    sub = number[4:]
    if re.fullmatch(r"(\d)\1{6}", sub):                                   # 9999999
        return False
    if sub in "01234567890" or sub in "09876543210":                      # 1234567
        return False
    if re.fullmatch(r"(\d)(\d)(?:\1\2)+\1?", sub):                        # 1212121
        return False
    return True


def name_error(value, label, allow_space=False):
    pattern = r"[A-Z][a-zA-Z' -]{1,29}" if allow_space else r"[A-Z][a-zA-Z'-]{1,29}"
    if not value:
        return f"{label} is required."
    if not re.fullmatch(pattern, value):
        return f"{label} must start with a capital letter and contain letters only (2-30 characters)."
    if value.lower() in INVALID_NAMES:
        return f"Please enter your actual {label.lower()}."
    if (not re.search(r"[aeiou]", value, re.I) or re.search(r"(.)\1{3,}", value)
            or (len(value) > 12 and not re.search(r"[\s-]", value))):
        return f"Please enter a valid {label.lower()}."
    return None


def email_error(email):
    if not email:
        return "Email is required."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return "Invalid email format."
    name, domain = email.lower().split("@", 1)
    is_gmail = domain == "gmail.com"
    is_agency = is_agency_domain(domain)
    if not is_gmail and not is_agency:
        return "Please use a Gmail address or an agency/school email (.edu, .gov, .mil, .org, .edu.ph, .gov.ph, etc.)."
    if is_gmail and len(name) < 5:
        return "Gmail username must be at least 5 characters."
    if is_gmail and not re.fullmatch(r"[a-z0-9.]+", name):
        return "Invalid Gmail username."
    if is_agency and not is_gmail and not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name):
        return "Invalid email username."
    if name in FAKE_EMAILS:
        return "Please enter your actual email address."
    return None


def contact_error(contact):
    if not contact:
        return "Contact Number is required."
    if not re.fullmatch(r"09[0-9]{9}", contact):
        return "Contact Number must start with 09 and contain exactly 11 digits."
    if not is_ph_mobile(contact):
        return "Please enter a real Philippine mobile number (example format: 09XXXXXXXXX)."
    return None


def username_error(username):
    if not username:
        return "Username is required."
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{4,19}", username):
        return "Username must start with a letter and be 5-20 characters long (letters, numbers, underscore)."
    return None


def password_error(password, confirm=None):
    if not password:
        return "Password is required."
    if len(password) < 6:
        return "Password must be at least 6 characters."
    if confirm is not None and password != confirm:
        return "Passwords do not match."
    return None


def validate_register(f):
    """f = dict of form values. Returns a list of error messages (empty list = valid)."""
    checks = [
        name_error(f.get("firstname", ""), "First Name"),
        name_error(f.get("lastname", ""), "Last Name", allow_space=True),
        email_error(f.get("email", "")),
        contact_error(f.get("contact", "")),
        username_error(f.get("username", "")),
        password_error(f.get("password", ""), f.get("confirm", "")),
    ]
    return [c for c in checks if c]
