import os, uuid, zipfile, subprocess, threading
from flask import Flask, request, jsonify, send_file, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

UPLOAD_FOLDER = '/tmp/docx_converter/uploads'
OUTPUT_FOLDER = '/tmp/docx_converter/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
jobs = {}

HTML = open(os.path.join(os.path.dirname(__file__), 'index.html')).read()

@app.route('/')
def index():
    return HTML

@app.route('/convert', methods=['POST'])
def convert():
    if 'files' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    uploaded = request.files.getlist('files')
    if len(uploaded) > 20:
        return jsonify({'error': 'Máximo de 20 arquivos por vez'}), 400
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOAD_FOLDER, job_id)
    out_dir = os.path.join(OUTPUT_FOLDER, job_id)
    os.makedirs(job_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    file_map = {}
    saved_files = []
    for f in uploaded:
        if not f.filename: continue
        orig_name = f.filename
        safe_name = secure_filename(f.filename) or f'file_{uuid.uuid4().hex[:8]}.docx'
        base, ext = os.path.splitext(safe_name)
        counter = 0
        unique_name = safe_name
        while unique_name in [x[1] for x in saved_files]:
            counter += 1; unique_name = f"{base}_{counter}{ext}"
        path = os.path.join(job_dir, unique_name)
        f.save(path)
        saved_files.append((orig_name, unique_name, path))
        file_map[orig_name] = unique_name
    jobs[job_id] = {'files': {name: {'status': 'converting', 'pdf_path': None, 'error': None} for _, name, _ in saved_files}, 'out_dir': out_dir}
    def do_convert():
        for orig, name, fpath in saved_files:
            try:
                result = subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', out_dir, fpath], capture_output=True, text=True, timeout=120)
                pdf_path = os.path.join(out_dir, os.path.splitext(name)[0] + '.pdf')
                if os.path.exists(pdf_path):
                    jobs[job_id]['files'][name].update({'status': 'done', 'pdf_path': pdf_path})
                else:
                    jobs[job_id]['files'][name].update({'status': 'error', 'error': result.stderr[:200] or 'PDF não gerado'})
            except subprocess.TimeoutExpired:
                jobs[job_id]['files'][name].update({'status': 'error', 'error': 'Tempo limite excedido'})
            except Exception as e:
                jobs[job_id]['files'][name].update({'status': 'error', 'error': str(e)[:200]})
    threading.Thread(target=do_convert, daemon=True).start()
    return jsonify({'job_id': job_id, 'file_map': file_map})

@app.route('/status/<job_id>')
def status(job_id):
    if job_id not in jobs: return jsonify({'error': 'Job não encontrado'}), 404
    return jsonify({'files': jobs[job_id]['files']})

@app.route('/download/<job_id>/<filename>')
def download(job_id, filename):
    if job_id not in jobs: return 'Job não encontrado', 404
    pdf_path = os.path.join(OUTPUT_FOLDER, job_id, os.path.splitext(filename)[0] + '.pdf')
    if not os.path.exists(pdf_path): return 'PDF não encontrado', 404
    return send_file(pdf_path, as_attachment=True, download_name=os.path.splitext(filename)[0] + '.pdf', mimetype='application/pdf')

@app.route('/zip/<job_id>')
def download_zip(job_id):
    if job_id not in jobs: return 'Job não encontrado', 404
    zip_path = os.path.join(OUTPUT_FOLDER, job_id, 'all_pdfs.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, info in jobs[job_id]['files'].items():
            if info['status'] == 'done' and info['pdf_path']:
                zf.write(info['pdf_path'], os.path.basename(info['pdf_path']))
    return send_file(zip_path, as_attachment=True, download_name='documentos_convertidos.zip', mimetype='application/zip')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    app.run(host='0.0.0.0', port=port, debug=False)
