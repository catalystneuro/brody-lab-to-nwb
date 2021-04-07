# brody-lab-to-nwb
Repository for the NWB conversion and processing codes for the Brody lab.

We provide an env file to create a conda environment. 
From the terminal, run:

```bash
conda env create -f brody-env.yml
conda activate brodylab
```

Once in the `brodylab` environment, clone this repo by
```
git clone https://github.com/catalystneuro/brody-lab-to-nwb
```
and then
```
pip install -e brody-lab-to-nwb
```


Note that access to the Neuralynx and Spikegadgets interfaces may depend on certain PRs/branches on python-neo, will
try to keep this up to date as those roll out.