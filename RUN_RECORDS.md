# Raw run records

The raw run records of the study (the `runs/` folder: 343,722 gzip-compressed files) are deposited with the archived copy of this
package on Zenodo (DOI 10.5281/zenodo.24241094) as the separate file `pandas3-drift-run-records.zip` (530,740,547 bytes, sha256
`d883615e7f1de3fe9c30f0e10f524ece207bc971f1b74f989855c0fac193e182`); they are not kept in the Git repository because of their size. In 79,897 run
records local folder paths were replaced by `<workspace>`, `<scratch>` or `<home>`; the archive lists them in its `CHANGED_FILES.tsv`.
The statistics and the secondary tools read `results/per_program.jsonl`, the per-program outcome table that the analyzer produces
from the run records; the run records are the input of that step (README, "Re-run the analysis", step 2).
