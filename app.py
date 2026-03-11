from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

votes = {
    'total': 0,
    'subjects': {
        'Subject A': 0,
        'Subject B': 0,
        'Subject C': 0
    }
}

@app.route('/')
def index():
    return render_template('index.html', votes=votes)

@app.route('/vote', methods=['POST'])
def vote():
    global votes
    subject = request.form.get('subject', 'Subject A')
    votes['total'] += 1
    votes['subjects'][subject] += 1
    return jsonify(votes)

if __name__ == '__main__':
    app.run(debug=True)