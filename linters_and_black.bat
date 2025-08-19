echo 'Formatting code with black...'
python -m black src/pynaneye
echo 'Running mypy...'
python -m mypy src/pynaneye
echo 'Running flake8...'
python -m flake8 src/pynaneye
