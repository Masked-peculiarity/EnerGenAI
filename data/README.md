# Forecast dataset

The single raw dataset is [../energydata_complete.csv](../energydata_complete.csv); it is not duplicated in this folder.

## Restore a missing dataset

Run from the repository root, not from energy-backend:

```powershell
if (-not (Test-Path energydata_complete.csv)) {
    Invoke-WebRequest -Uri "https://archive.ics.uci.edu/ml/machine-learning-databases/00374/energydata_complete.csv" -OutFile energydata_complete.csv
}
Get-FileHash energydata_complete.csv -Algorithm SHA256
```

The SHA256 must match the value below and the trained model metadata. Do not resave or fabricate data to bypass this check. If the original CSV is elsewhere, set DATASET_PATH to its absolute path in the root .env and restart. Startup deliberately requires local data; it does not silently download data or retrain models.

Source: [UCI Appliances Energy Prediction](https://archive.ics.uci.edu/dataset/374/appliances%2Benergy%2Bprediction), Candanedo, Feldheim and Deramaix (2017), DOI10.24432/C5VC8G,CC BY4.0. Preserve attribution when redistributing.

19,735 observations,2016-01-11T17:00 through2016-05-27T18:00,ten-minute intervals. Appliances/lights are Wh per interval. Date timezone unspecified. Actual pressure column Press_mm_hg. rv1/rv2 controls are excluded.

SHA256:2820bf712ad0275cb18b85a05250926100d8e65ebb9f4d2d016ca91ea152a25d

Active loader: energy-backend/ml/data/load_data.py. Rejects schema/type/missing/duplicate/gap/physical-range defects. Reproduction/training commands are in PROJECT_GUIDE.md.

Do not let Excel permanently convert large numeric/text fields and resave the raw CSV. Preserve the original byte content; models validate the file hash. The old Energy_consumption.csv notebooks are not the production training pipeline.

One household is not general evidence of other homes or appliance-level NILM.

## Household-profile predictor dataset

recs2020_predictor.csv is the 18,496-row feature/target subset of the official EIA 2020 RECS public v7 file. Its annual KWH target is separate from UCI's ten-minute appliance energy. The predictor training script records exact subset hashes and never mixes incompatible target units. See [prediction guide](../PREDICTION_GUIDE.md) for source URLs, verified codebook definitions, exclusions, evaluation and reproduction.
