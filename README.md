# przemienniki-FT-5D

Generate list of FT5D memory channels based on polish website https://przemienniki.net

This may be only usefull for polish users.

The format is compatible with ADMS-11 to ADMS-14.

More info https://www.repeaterbook.com/wiki/doku.php?id=yaesu_adms_11#supported_searches


## Important Warning
**Before** using this program, **make a backup of your FT5D configuration**. This software is provided as-is, without any warranty of any kind. The author is not responsible for any damage, loss of data, or other issues that may arise from using this program or data in the repository !

## Usage
You can generate the list by running `gen.py` script or you can import `adms14_ft5d.csv` file to **FT5D Programmer ADMS-14**. Should wordk with FT3D too.

```
pip install -r requirements.txt
./gen.py JO90vd 100
```

## Steps needed to update via microSD Card
1. Backup your yaesu to microsd
2. Move to your PC
3. In ADMS-14 (or earlier) Communication->Get Data From SD card
4. File->Import and select the csv file from SD card
5. At this point you should have all the new entries
6. Sort to your needs by selecting Edit->Sort
7. Communication->Send Data to SD card
8. Move your micro SD card to your yaesu
9. On FT5D: Menu->SD CARD-BACKUP->Read from SD
10. voila !

Note: I'm not putting `BACKUP.dat` file here, for obvious reasons.

## License

See the LICENSE file.
