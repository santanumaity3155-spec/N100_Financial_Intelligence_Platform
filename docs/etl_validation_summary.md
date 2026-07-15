# ETL Validation Summary Report

**Sprint 1 - Task 3**

**Generated:** 2026-07-15 23:07:22

---

## Executive Summary

### Overall Status: **FAIL**

This report validates the ETL pipeline execution and data quality for Sprint 1. The validation covers database integrity, foreign key constraints, load audit, and data quality checks.

---

## 1. Companies Count Validation

### Requirement: SELECT COUNT(*) FROM companies

- **Total Companies:** 92
- **Status:** PASS

✅ Companies table contains records and is ready for analysis.

---

## 2. Foreign Key Integrity Check

### Requirement: PRAGMA foreign_key_check

- **Total Violations:** 434
- **Status:** FAIL

❌ Foreign key violations found:

  - Table: pros_cons, RowID: 12, Parent: companies, FK: 0
  - Table: documents, RowID: 1458, Parent: companies, FK: 0
  - Table: documents, RowID: 1459, Parent: companies, FK: 0
  - Table: documents, RowID: 1460, Parent: companies, FK: 0
  - Table: documents, RowID: 1461, Parent: companies, FK: 0
  - Table: documents, RowID: 1462, Parent: companies, FK: 0
  - Table: documents, RowID: 1463, Parent: companies, FK: 0
  - Table: documents, RowID: 1464, Parent: companies, FK: 0
  - Table: documents, RowID: 1465, Parent: companies, FK: 0
  - Table: documents, RowID: 1466, Parent: companies, FK: 0
  - Table: documents, RowID: 1467, Parent: companies, FK: 0
  - Table: documents, RowID: 1468, Parent: companies, FK: 0
  - Table: documents, RowID: 1469, Parent: companies, FK: 0
  - Table: documents, RowID: 1470, Parent: companies, FK: 0
  - Table: documents, RowID: 1471, Parent: companies, FK: 0
  - Table: documents, RowID: 1472, Parent: companies, FK: 0
  - Table: documents, RowID: 1473, Parent: companies, FK: 0
  - Table: documents, RowID: 1474, Parent: companies, FK: 0
  - Table: documents, RowID: 1475, Parent: companies, FK: 0
  - Table: documents, RowID: 1476, Parent: companies, FK: 0
  - Table: documents, RowID: 1477, Parent: companies, FK: 0
  - Table: documents, RowID: 1478, Parent: companies, FK: 0
  - Table: documents, RowID: 1479, Parent: companies, FK: 0
  - Table: documents, RowID: 1480, Parent: companies, FK: 0
  - Table: documents, RowID: 1481, Parent: companies, FK: 0
  - Table: documents, RowID: 1482, Parent: companies, FK: 0
  - Table: documents, RowID: 1483, Parent: companies, FK: 0
  - Table: documents, RowID: 1484, Parent: companies, FK: 0
  - Table: documents, RowID: 1485, Parent: companies, FK: 0
  - Table: documents, RowID: 1486, Parent: companies, FK: 0
  - Table: documents, RowID: 1487, Parent: companies, FK: 0
  - Table: documents, RowID: 1488, Parent: companies, FK: 0
  - Table: documents, RowID: 1489, Parent: companies, FK: 0
  - Table: documents, RowID: 1490, Parent: companies, FK: 0
  - Table: documents, RowID: 1491, Parent: companies, FK: 0
  - Table: documents, RowID: 1492, Parent: companies, FK: 0
  - Table: documents, RowID: 1493, Parent: companies, FK: 0
  - Table: documents, RowID: 1494, Parent: companies, FK: 0
  - Table: documents, RowID: 1495, Parent: companies, FK: 0
  - Table: documents, RowID: 1496, Parent: companies, FK: 0
  - Table: documents, RowID: 1497, Parent: companies, FK: 0
  - Table: documents, RowID: 1498, Parent: companies, FK: 0
  - Table: documents, RowID: 1499, Parent: companies, FK: 0
  - Table: documents, RowID: 1500, Parent: companies, FK: 0
  - Table: documents, RowID: 1501, Parent: companies, FK: 0
  - Table: documents, RowID: 1502, Parent: companies, FK: 0
  - Table: documents, RowID: 1503, Parent: companies, FK: 0
  - Table: documents, RowID: 1504, Parent: companies, FK: 0
  - Table: documents, RowID: 1505, Parent: companies, FK: 0
  - Table: documents, RowID: 1506, Parent: companies, FK: 0
  - Table: documents, RowID: 1507, Parent: companies, FK: 0
  - Table: documents, RowID: 1508, Parent: companies, FK: 0
  - Table: documents, RowID: 1509, Parent: companies, FK: 0
  - Table: documents, RowID: 1510, Parent: companies, FK: 0
  - Table: documents, RowID: 1511, Parent: companies, FK: 0
  - Table: documents, RowID: 1512, Parent: companies, FK: 0
  - Table: documents, RowID: 1513, Parent: companies, FK: 0
  - Table: documents, RowID: 1514, Parent: companies, FK: 0
  - Table: documents, RowID: 1515, Parent: companies, FK: 0
  - Table: documents, RowID: 1516, Parent: companies, FK: 0
  - Table: documents, RowID: 1517, Parent: companies, FK: 0
  - Table: documents, RowID: 1518, Parent: companies, FK: 0
  - Table: documents, RowID: 1519, Parent: companies, FK: 0
  - Table: documents, RowID: 1520, Parent: companies, FK: 0
  - Table: documents, RowID: 1521, Parent: companies, FK: 0
  - Table: documents, RowID: 1522, Parent: companies, FK: 0
  - Table: documents, RowID: 1523, Parent: companies, FK: 0
  - Table: documents, RowID: 1524, Parent: companies, FK: 0
  - Table: documents, RowID: 1525, Parent: companies, FK: 0
  - Table: documents, RowID: 1526, Parent: companies, FK: 0
  - Table: documents, RowID: 1527, Parent: companies, FK: 0
  - Table: documents, RowID: 1528, Parent: companies, FK: 0
  - Table: documents, RowID: 1529, Parent: companies, FK: 0
  - Table: documents, RowID: 1530, Parent: companies, FK: 0
  - Table: documents, RowID: 1531, Parent: companies, FK: 0
  - Table: documents, RowID: 1532, Parent: companies, FK: 0
  - Table: documents, RowID: 1533, Parent: companies, FK: 0
  - Table: documents, RowID: 1534, Parent: companies, FK: 0
  - Table: documents, RowID: 1535, Parent: companies, FK: 0
  - Table: documents, RowID: 1536, Parent: companies, FK: 0
  - Table: documents, RowID: 1537, Parent: companies, FK: 0
  - Table: documents, RowID: 1538, Parent: companies, FK: 0
  - Table: documents, RowID: 1539, Parent: companies, FK: 0
  - Table: documents, RowID: 1540, Parent: companies, FK: 0
  - Table: documents, RowID: 1541, Parent: companies, FK: 0
  - Table: documents, RowID: 1542, Parent: companies, FK: 0
  - Table: documents, RowID: 1543, Parent: companies, FK: 0
  - Table: documents, RowID: 1544, Parent: companies, FK: 0
  - Table: documents, RowID: 1545, Parent: companies, FK: 0
  - Table: documents, RowID: 1546, Parent: companies, FK: 0
  - Table: documents, RowID: 1547, Parent: companies, FK: 0
  - Table: documents, RowID: 1548, Parent: companies, FK: 0
  - Table: documents, RowID: 1549, Parent: companies, FK: 0
  - Table: documents, RowID: 1550, Parent: companies, FK: 0
  - Table: documents, RowID: 1551, Parent: companies, FK: 0
  - Table: documents, RowID: 1552, Parent: companies, FK: 0
  - Table: documents, RowID: 1553, Parent: companies, FK: 0
  - Table: documents, RowID: 1554, Parent: companies, FK: 0
  - Table: documents, RowID: 1555, Parent: companies, FK: 0
  - Table: documents, RowID: 1556, Parent: companies, FK: 0
  - Table: documents, RowID: 1557, Parent: companies, FK: 0
  - Table: documents, RowID: 1558, Parent: companies, FK: 0
  - Table: documents, RowID: 1559, Parent: companies, FK: 0
  - Table: documents, RowID: 1560, Parent: companies, FK: 0
  - Table: documents, RowID: 1561, Parent: companies, FK: 0
  - Table: documents, RowID: 1562, Parent: companies, FK: 0
  - Table: documents, RowID: 1563, Parent: companies, FK: 0
  - Table: documents, RowID: 1564, Parent: companies, FK: 0
  - Table: documents, RowID: 1565, Parent: companies, FK: 0
  - Table: documents, RowID: 1566, Parent: companies, FK: 0
  - Table: documents, RowID: 1567, Parent: companies, FK: 0
  - Table: documents, RowID: 1568, Parent: companies, FK: 0
  - Table: documents, RowID: 1569, Parent: companies, FK: 0
  - Table: documents, RowID: 1570, Parent: companies, FK: 0
  - Table: documents, RowID: 1571, Parent: companies, FK: 0
  - Table: documents, RowID: 1572, Parent: companies, FK: 0
  - Table: documents, RowID: 1573, Parent: companies, FK: 0
  - Table: documents, RowID: 1574, Parent: companies, FK: 0
  - Table: documents, RowID: 1575, Parent: companies, FK: 0
  - Table: documents, RowID: 1576, Parent: companies, FK: 0
  - Table: documents, RowID: 1577, Parent: companies, FK: 0
  - Table: documents, RowID: 1578, Parent: companies, FK: 0
  - Table: documents, RowID: 1579, Parent: companies, FK: 0
  - Table: documents, RowID: 1580, Parent: companies, FK: 0
  - Table: documents, RowID: 1581, Parent: companies, FK: 0
  - Table: documents, RowID: 1582, Parent: companies, FK: 0
  - Table: documents, RowID: 1583, Parent: companies, FK: 0
  - Table: documents, RowID: 1584, Parent: companies, FK: 0
  - Table: documents, RowID: 1585, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 189, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 190, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 191, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 192, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 193, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 194, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 195, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1170, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1171, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1172, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1173, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1174, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1175, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1176, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1177, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1178, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1179, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1180, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1181, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1182, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1183, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1184, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1185, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1186, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1187, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1188, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1189, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1190, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1191, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1192, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1193, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1194, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1195, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1196, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1197, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1198, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1199, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1200, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1201, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1202, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1203, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1204, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1205, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1206, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1207, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1208, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1209, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1210, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1211, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1212, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1213, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1214, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1215, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1216, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1217, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1218, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1219, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1220, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1221, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1222, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1223, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1224, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1225, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1226, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1227, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1228, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1229, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1230, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1231, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1232, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1233, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1234, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1235, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1236, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1237, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1238, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1239, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1240, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1241, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1242, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1243, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1244, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1245, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1246, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1247, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1248, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1249, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1250, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1251, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1252, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1253, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1254, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1255, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1256, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1257, Parent: companies, FK: 0
  - Table: cash_flow, RowID: 1258, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1149, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1150, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1151, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1152, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1153, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1154, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1155, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1156, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1157, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1158, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1159, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1160, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1161, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1162, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1163, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1164, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1165, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1166, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1167, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1168, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1169, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1170, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1171, Parent: companies, FK: 0
  - Table: financial_ratios, RowID: 1172, Parent: companies, FK: 0
  - Table: analysis, RowID: 17, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1200, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1201, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1202, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1203, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1204, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1205, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1206, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1207, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1208, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1209, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1210, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1211, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1212, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1226, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1227, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1228, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1229, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1230, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1231, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1232, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1233, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1234, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1235, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1236, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1237, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1238, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1239, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1240, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1241, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1242, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1243, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1244, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1245, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1246, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1247, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1248, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1249, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1250, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1251, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1252, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1253, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1254, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1255, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1256, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1257, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1258, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1259, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1285, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1286, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1287, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1288, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1289, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1290, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1291, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1292, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1293, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1294, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1295, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1296, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1297, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1298, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1299, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1300, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1301, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1302, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1303, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1304, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1305, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1306, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1307, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1308, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1309, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1323, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1324, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1325, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1326, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1327, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1328, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1329, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1330, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1331, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1332, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1333, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1334, Parent: companies, FK: 0
  - Table: balance_sheet, RowID: 1335, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1263, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1264, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1265, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1266, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1267, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1268, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1269, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1270, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1271, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1272, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1273, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1274, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1275, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1276, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1277, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1278, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1279, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1280, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1281, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1282, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1283, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1284, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1285, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1286, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1287, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1288, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1289, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1290, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1291, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1292, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1293, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1294, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1295, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1296, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1297, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1298, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1299, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1300, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1301, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1302, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1303, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1304, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1305, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1306, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1307, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1308, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1309, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1310, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1311, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1312, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1313, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1314, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1315, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1316, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1317, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1318, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1319, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1320, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1321, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1322, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1323, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1324, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1325, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1326, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1327, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1328, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1329, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1330, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1331, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1332, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1333, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1334, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1335, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1336, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1337, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1338, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1339, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1340, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1341, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1342, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1343, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1344, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1345, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1346, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1347, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1348, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1349, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1350, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1351, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1352, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1353, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1354, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1355, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1356, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1357, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1358, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1359, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1360, Parent: companies, FK: 0
  - Table: profit_loss, RowID: 1361, Parent: companies, FK: 0

---

## 3. Load Audit Validation

### Requirement: Load audit file (load_audit.csv)

- **Status:** FAIL
- **Message:** load_audit.csv not found

❌ Load audit file not found.

---

## 4. Validation Report Check

### Requirement: Validation report (validation_failures.csv)

- **Status:** FAIL
- **Message:** validation_failures.csv not found

❌ Validation report not found.

---

## 5. Database Tables Validation

### Requirement: All expected tables exist with data


| Table | Exists | Records | Status |
|-------|--------|---------|--------|
| companies | ✅ | 92 | ✅ |
| profit_loss | ✅ | 1263 | ✅ |
| balance_sheet | ✅ | 1225 | ✅ |
| cash_flow | ✅ | 1164 | ✅ |
| sectors | ✅ | 92 | ✅ |
| stock_prices | ✅ | 5520 | ✅ |
| market_cap | ✅ | 92 | ✅ |
| financial_ratios | ✅ | 1065 | ✅ |
| financial_kpis | ✅ | 1164 | ✅ |
| peer_groups | ✅ | 56 | ✅ |
| analysis | ✅ | 5 | ✅ |
| documents | ✅ | 1585 | ✅ |
| pros_cons | ✅ | 5 | ✅ |

✅ All expected tables exist and contain data.

---

## 6. Data Integrity Check

### Requirement: No orphaned records or duplicates


#### Orphaned Records

- Profit & Loss: 99
- Balance Sheet: 85
- Cash Flow: 96
- Sectors: 0

#### Duplicate Records

- Profit & Loss: 0
- Balance Sheet: 0
- Cash Flow: 0

- **Total Issues:** 280
- **Status:** WARNING

⚠️ Data integrity issues detected. Review recommended.

---

## Sprint 1 Exit Criteria Assessment


| Criteria | Status |
|----------|--------|
| Companies count > 0 | ✅ |
| No foreign key violations | ❌ |
| Load audit exists and successful | ❌ |
| Validation report exists | ❌ |
| All tables exist with data | ✅ |
| No critical data integrity issues | ✅ |

### ❌ **Sprint 1 Exit Criteria: NOT SATISFIED**

Some exit criteria have not been met. Please review the issues above and take corrective action.

---

## Recommendations

2. **Critical:** Fix foreign key violations to maintain referential integrity.
3. **High:** Investigate and fix load audit failures.
4. **High:** Address critical validation failures before proceeding.
5. **Medium:** Review and resolve data integrity issues (orphaned records or duplicates).

---

## Conclusion

The ETL pipeline has some validation issues that need to be addressed before Sprint 1 can be considered complete. Please review the recommendations above and take necessary corrective actions.
