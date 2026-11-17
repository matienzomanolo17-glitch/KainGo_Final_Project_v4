// Client-side validation. Same rules as validators.py (ported from manolo_real); the server checks again.
const BAD_NAMES = ["hello","test","admin","unknown","sample","asdf","asdfgh","qwerty","qwertyuiop","zxcvbn","abc","name"];
const FAKE_EMAILS = ["admin","test","hello","sample","asdf","qwerty","gmail","user","unknown","abc123","12345"];
const TOP = ["edu","gov","mil","org","int"], SECOND = ["edu","gov","ac","go","sch","org","mil"];
const PREFIXES = ("0905 0906 0915 0916 0917 0926 0927 0935 0936 0937 0945 0953 0954 0955 0956 0965 0966 0967 0975 0976 " +
  "0977 0978 0979 0995 0996 0997 0907 0908 0909 0910 0911 0912 0913 0914 0918 0919 0920 0921 0922 0923 0924 0925 0928 " +
  "0929 0930 0931 0932 0933 0934 0938 0939 0940 0941 0942 0943 0944 0946 0947 0948 0949 0950 0951 0961 0963 0968 0969 " +
  "0970 0973 0974 0981 0989 0998 0999 0991 0992 0993 0994").split(" ");

function nameError(v, label, allowSpace) {
  if (!v) return label + " is required.";
  const re = allowSpace ? /^[A-Z][a-zA-Z' -]{1,29}$/ : /^[A-Z][a-zA-Z'-]{1,29}$/;
  if (!re.test(v)) return label + " must start with a capital letter and contain letters only.";
  if (BAD_NAMES.includes(v.toLowerCase())) return "Please enter your actual " + label.toLowerCase() + ".";
  if (!/[aeiou]/i.test(v) || /(.)\1{3,}/.test(v) || (v.length > 12 && !/[\s-]/.test(v))) return "Please enter a valid " + label.toLowerCase() + ".";
  return "";
}
function emailError(v) {
  if (!v) return "Email is required.";
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v)) return "Invalid email format.";
  const [name, domain] = v.toLowerCase().split("@");
  const labels = domain.split("."), last = labels[labels.length - 1];
  const gmail = domain === "gmail.com";
  const agency = TOP.includes(last) || (labels.length >= 3 && /^[a-z]{2}$/.test(last) && SECOND.includes(labels[labels.length - 2]));
  if (!gmail && !agency) return "Please use a Gmail address or an agency/school email (.edu, .gov, .mil, .org, .edu.ph, .gov.ph, etc.).";
  if (gmail && name.length < 5) return "Gmail username must be at least 5 characters.";
  if (gmail && !/^[a-z0-9.]+$/.test(name)) return "Invalid Gmail username.";
  if (!gmail && !/^[a-z0-9][a-z0-9._-]*$/.test(name)) return "Invalid email username.";
  if (FAKE_EMAILS.includes(name)) return "Please enter your actual email address.";
  return "";
}
function contactError(v) {
  if (!v) return "Contact Number is required.";
  if (!/^09[0-9]{9}$/.test(v)) return "Contact Number must start with 09 and contain exactly 11 digits.";
  const sub = v.slice(4);
  if (!PREFIXES.includes(v.slice(0, 4)) || /^(\d)\1{6}$/.test(sub) || "01234567890".includes(sub) ||
      "09876543210".includes(sub) || /^(\d)(\d)(?:\1\2)+\1?$/.test(sub))
    return "Please enter a real Philippine mobile number (example format: 09XXXXXXXXX).";
  return "";
}
const RULES = {
  name: v => nameError(v, "First Name", false),
  lastname: v => nameError(v, "Last Name", true),
  email: emailError,
  contact: contactError,
  username: v => !v ? "Username is required." : (/^[A-Za-z][A-Za-z0-9_]{4,19}$/.test(v) ? "" : "Username must start with a letter and be 5-20 characters long."),
  password: v => !v ? "Password is required." : (v.length < 6 ? "Password must be at least 6 characters." : ""),
  confirm: (v, form) => v !== form.querySelector("#password").value ? "Passwords do not match." : ""
};

function showError(input, msg) {
  let fb = input.nextElementSibling;
  while (fb && !fb.classList.contains("invalid-feedback")) {
    if (fb.tagName === "INPUT" || fb.tagName === "TEXTAREA") { fb = null; break; }
    fb = fb.nextElementSibling;
  }
  if (!fb) { fb = document.createElement("div"); fb.className = "invalid-feedback"; input.insertAdjacentElement("afterend", fb); }
  fb.textContent = msg;
  input.classList.toggle("is-invalid", !!msg);
  input.classList.toggle("is-valid", !msg && input.value !== "");
}
function checkInput(input) {
  const msg = RULES[input.dataset.rule](input.value.trim() === input.value || input.type === "password" ? input.value : input.value.trim(), input.form);
  showError(input, msg);
  return !msg;
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form").forEach(form => {
    const inputs = form.querySelectorAll("[data-rule]");
    if (!inputs.length) return;
    inputs.forEach(i => i.addEventListener("blur", () => checkInput(i)));
    form.addEventListener("submit", e => {
      let ok = true;
      inputs.forEach(i => { if (!checkInput(i)) ok = false; });
      if (!ok) { e.preventDefault(); const bad = form.querySelector(".is-invalid"); if (bad) bad.focus(); }
    });
  });
  // contact number: digits only, max 11
  document.querySelectorAll("#contact").forEach(c => c.addEventListener("input", () => { c.value = c.value.replace(/[^0-9]/g, "").slice(0, 11); }));
  const show = document.getElementById("showPw");
  if (show && document.getElementById("confirm")) show.addEventListener("change", () => {
    ["password", "confirm"].forEach(id => document.getElementById(id).type = show.checked ? "text" : "password");
  });
});
