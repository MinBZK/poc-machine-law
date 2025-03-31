How to create

```bash
cd gopy_machine

../script/gopy-build.sh --package=github.com/minbzk/poc-machine-law/machinev2/service --verbose --output=gopy_machine

python3 setup.py bdist_wheel

cd ../ 

uv pip install ./gopy_machine/dist/gopy_machine-0.0.0-py3-none-any.whl 
```