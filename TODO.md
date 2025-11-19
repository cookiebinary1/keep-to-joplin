
-json je vo formate:

{
  "color": "DEFAULT",
  "isTrashed": false,
  "isPinned": false,
  "isArchived": false,
  "textContent": "servis\nbdb50388c4\n",
  "title": "dispecer",
  "userEditedTimestampUsec": 1630312783380000,
  "createdTimestampUsec": 1630312769935000,
  "textContentHtml": "<p dir=\"ltr\" style=\"line-height:1.38;margin-top:0.0pt;margin-bottom:0.0pt;\"><span style=\"font-size:7.2pt;font-family:'Google Sans';color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">servis<\/span><\/p><p dir=\"ltr\" style=\"line-height:1.38;margin-top:0.0pt;margin-bottom:0.0pt;\"><span style=\"font-size:7.2pt;font-family:'Google Sans';color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">bdb50388c4<\/span><\/p>"
}
alebo ked je zoznam, tak:

{
  "color": "DEFAULT",
  "isTrashed": false,
  "isPinned": true,
  "isArchived": false,
  "listContent": [
    {
      "textHtml": "<p dir=\"ltr\" style=\"line-height:1.38;margin-top:0.0pt;margin-bottom:0.0pt;\"><span style=\"font-size:7.2pt;font-family:'Google Sans';color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">sudo airmon-ng start wlan0<\/span><\/p>",
      "text": "sudo airmon-ng start wlan0",
      "isChecked": false
    },
    {
      "textHtml": "<p dir=\"ltr\" style=\"line-height:1.38;margin-top:0.0pt;margin-bottom:0.0pt;\"><span style=\"font-size:7.2pt;font-family:'Google Sans';color:#000000;background-color:transparent;font-weight:400;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;white-space:pre-wrap;\">sudo iwconfig<\/span><\/p>",
      "text": "sudo iwconfig",
      "isChecked": false
    },
    ....
  ],
  "title": "kali",
  "userEditedTimestampUsec": 1762984210628000,
  "createdTimestampUsec": 1762983782764000
}


- cize dodrzme farbu, pokial je nastavena
- obsah poznamky je v poli "textContent" alebo "text" pri listContente 
- title nastavme "title" pokial existuje 
- chceme mat zoradene poznamky podla userEditedTimestampUsec posledne nech je hore prve

- isPinned su prve
- isArchived a isTrashed neimportujme
