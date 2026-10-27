from pathlib import Path
import importlib.util,json,os,sys,subprocess
root=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment');state=json.loads((root/'design_reference_state.json').read_text());skill=Path(r'C:\Users\jaskew\.codex\plugins\cache\openai-primary-runtime\documents\26.1020.11348\skills\documents\render_docx.py')
os.environ['PATH']=r'C:\Users\jaskew\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin'+os.pathsep+os.environ['PATH']
spec=importlib.util.spec_from_file_location('htoc_docx_renderer',skill);renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
def word_conversion(doc_path,user_profile,out_dir,stem,verbose=False):
 pdf=Path(out_dir)/(stem+'.pdf');cmd=[r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe','-NoProfile','-STA','-ExecutionPolicy','Bypass','-File',str(root/'native_validation/render_design_guide_word.ps1'),'-InputPath',str(Path(doc_path).resolve()),'-OutputPath',str(pdf)]
 result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120,creationflags=subprocess.CREATE_NO_WINDOW)
 if result.returncode!=0 or not pdf.exists():raise RuntimeError(result.stdout)
 return str(pdf),result.stdout
renderer.convert_to_pdf=word_conversion
sys.argv=[str(skill),state['docx'],'--output_dir',str(Path(state['work'])/'render'),'--dpi','110']
renderer.main()
print('Native Microsoft Word conversion used; page PNGs created by bundled render_docx.py.')
