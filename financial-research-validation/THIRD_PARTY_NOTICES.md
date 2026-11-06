# Third-party dependencies

pandas is used under BSD-3-Clause; its resolved dependency versions are in `uv.lock`.
The test environment uses pytest (MIT) and Ruff (MIT). NumPy, python-dateutil, pytz and
tzdata, if resolved, retain their own licenses. Libraries are installed from package registries,
not vendored or relicensed by this project. Python, uv and CI actions retain their own terms.

Matplotlib generates the experiment chart. Matplotlib, contourpy, cycler, fonttools,
kiwisolver, packaging, Pillow, pyparsing and the bundled DejaVu fonts retain their
respective licenses; resolved versions and distributions are recorded in `uv.lock`.
