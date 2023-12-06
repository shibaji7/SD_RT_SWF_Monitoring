find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +
isort -rc -sl py/
autoflake --remove-all-unused-imports -i -r py/
isort -rc -m 3 py/
black py/

