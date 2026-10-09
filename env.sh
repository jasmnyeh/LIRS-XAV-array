# for my computer or else it'll fail at building wheel for llvmlite if directly pip3 install -r requirements.txt
conda create -n whoi python=3.11
conda activate whoi
conda install -c conda-forge numba llvmlite pandas dask pyqt
pip install ecosound