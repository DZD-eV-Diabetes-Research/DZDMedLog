# Drug Database

MedLog needs a drug database to power the medication search during interviews. The database is loaded into MedLog's own SQL store and queried locally — no external service is called at interview time.

> [!IMPORTANT]
> MedLog does **not** include a licensed drug database. You must either supply your own (see below) or use the built-in dummy dataset for development and demo purposes.

---

## Built-in Dummy Dataset

MedLog ships with a small dummy drug dataset that is used automatically when no real drug data source is configured. It contains a handful of made-up entries just enough to demonstrate the search and intake workflow.

To use it, set:

```
DRUG_IMPORTER_PLUGIN=DummyDrugImporterV1
```

This is the default value. No further configuration is needed.

> [!NOTE]
> The dummy dataset is not useful for real clinical data collection. It is only intended for demos, development, and automated tests.

---

## MMI Pharmindex (GKV Arzneimittelindex)

MedLog ships with a production-ready importer for the **MMI Pharmindex** (`GKV Arzneimittelindex`), a licensed German drug reference database published by MMI (Medi-Media Informations-GmbH).

> [!IMPORTANT]
> The MMI Pharmindex is a **licensed, proprietary database**. You must have a valid subscription with MMI to use it. MedLog does not include the data files and cannot help you obtain a license.
> Contact: [https://www.mmi.de](https://www.mmi.de)

To enable it:

```
DRUG_IMPORTER_PLUGIN=MMIPharmindex1_32
```

### Loading data manually

Upload a dataset via the admin section of the web UI, or trigger the import via the REST API endpoint `PUT /drug/db/update` (requires `DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB=true`).

### Automatic FTP updates

When MMI provides access via FTP, MedLog can poll for new dataset versions and import them automatically:

```
DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB=true
DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB=true
DRUG_IMPORTER_SOURCE_FTP_HOST=ftp.mmi.de
DRUG_IMPORTER_SOURCE_FTP_USER=<your-ftp-user>
DRUG_IMPORTER_SOURCE_FTP_PASSWORD=<your-ftp-password>
DRUG_IMPORTER_SOURCE_FTP_PORT=21
```

The check interval is controlled by `DRUG_IMPORTER_REMOTE_VERSION_CHECK_COOLDOWN_TIME_SEC` (default: 3600 s).

To restrict imports to specific hours of the day (UTC) — useful when multiple instances share a VM:

```
DRUG_IMPORTER_DATA_IMPORT_ALLOWED_HOURS=[2,3,4,5]
```

### Memory tuning

The import is a bulk operation. On low-memory machines, reduce the batch size:

```
DRUG_IMPORTER_BATCH_SIZE=50000   # default is 200000
```

---

## Writing Your Own Drug Importer Plugin

If you use a different drug database (national formulary, in-house drug catalogue, etc.) you can implement a custom importer plugin.

Plugins live in:

```
MedLog/backend/medlogserver/model/drug_data/
```

The two built-in plugins (`DummyDrugImporterV1`, `MMIPharmindex1_32`) serve as reference implementations. A plugin must:

1. Implement the base importer interface defined in that package.
2. Be registered in `DRUG_IMPORTER_PLUGIN` literal type in [config.py](../MedLog/backend/medlogserver/config.py).

There is no formal plugin API documentation yet. Reading the dummy importer source is the recommended starting point.

> [!NOTE]
> If you build an importer for a publicly redistributable drug dataset, consider contributing it back to the project via a pull request.
