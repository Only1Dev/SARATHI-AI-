with open("server.py", "r", encoding="utf-8") as f:
    text = f.read()

# Replace any literal newlines inside strings with \n
lines = text.split("\n")
for i in range(len(lines)):
    if 'msg = f"⚡ *Task Accepted!*' in lines[i]:
        lines[i] = '        msg = f"⚡ *Task Accepted!*\\n\\nYour task is now being worked on by {worker[\'name\']}.\\nRating: {worker[\'rating\']}"'
    elif 'msg = f"📦 *Deliverable Submitted!*' in lines[i]:
        lines[i] = '        msg = f"📦 *Deliverable Submitted!*\\n\\n• *Worker:* {task[\'workers\'][\'name\']}\\n• *Proof:* {deliv[\'text\']}\\n• *AI Verdict:* {audit_res.get(\'audit_summary\')}\\n\\nTap below to approve:"'

with open("server.py", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
