with open('public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('alert("Error sending SMS. Check console.");', 'alert("Firebase Error: " + error.message);')
# Let's also fix the worker dashboard link
text = text.replace('href="/worker"', 'href="/worker.html"')
with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
