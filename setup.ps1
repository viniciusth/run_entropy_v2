if (Test-Path "venv") {
  & ".\venv\Scripts\Activate.ps1"
}
else {
  python -m venv venv
  & ".\venv\Scripts\Activate.ps1"
  pip install -r requirements.txt
}
