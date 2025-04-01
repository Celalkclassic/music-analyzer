from flask import Flask, request, render_template
import music21
from music21 import converter, chord, roman, harmony
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def analyze_music(file_path):
    score = converter.parse(file_path)
    key = score.analyze('key')
    key_str = f"{key.tonic.name} {key.mode}"
    chords = []
    for part in score.parts:
        for measure in part.getElementsByClass('Measure'):
            notes = [n for n in measure.notes if hasattr(n, 'pitch')]
            if len(notes) > 1:
                chord_obj = chord.Chord([n.pitch for n in notes])
                roman_num = roman.romanNumeralFromChord(chord_obj, key)
                chords.append({
                    'measure': measure.measureNumber,
                    'chord': chord_obj.pitchedCommonName,
                    'roman': str(roman_num)
                })
    cadences = []
    for part in score.parts:
        measures = part.getElementsByClass('Measure')
        for i, measure in enumerate(measures[:-1]):
            current_chord = harmony.chordSymbolFromChord(measure.chordify())
            next_chord = harmony.chordSymbolFromChord(measures[i+1].chordify())
            if current_chord and next_chord:
                progression = (current_chord.figure, next_chord.figure)
                cadence_type = classify_cadence(progression)
                if cadence_type:
                    cadences.append({
                        'measure': measure.measureNumber,
                        'type': cadence_type,
                        'progression': f"{progression[0]} -> {progression[1]}"
                    })
    return {
        'key': key_str,
        'chords': chords[:5],
        'cadences': cadences
    }

def classify_cadence(progression):
    if progression[0].startswith('V') and progression[1].startswith('I'):
        return "Authentic"
    elif progression[0].startswith('IV') and progression[1].startswith('I'):
        return "Plagal"
    elif progression[0].startswith('V') and not progression[1].startswith('I'):
        return "Deceptive"
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Dosya seçilmedi!", 400
        file = request.files['file']
        if file.filename == '':
            return "Dosya adı boş!", 400
        if file and file.filename.endswith('.mid'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            file.save(file_path)
            results = analyze_music(file_path)
            return render_template('results.html', results=results)
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
