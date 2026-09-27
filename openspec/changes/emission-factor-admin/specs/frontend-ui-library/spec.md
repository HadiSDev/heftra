## ADDED Requirements

### Requirement: The UI library SHALL offer a file dropzone

`FileDropzone` SHALL let a user choose one file by dropping it or by browsing, and it SHALL:
- highlight while a file is dragged over it;
- refuse a file whose name or media type doesn't match `accept`, or that is larger than `maxBytes`, saying why;
- show the chosen file's name and size, with a way to remove it and to choose another;
- show an error passed in from outside;
- do nothing while disabled.

Its file input SHALL carry the accessible name it is given, and the browse control SHALL be reachable by keyboard.

#### Scenario: Dropping a file

- **WHEN** a user drops `ceda.xlsx` onto a dropzone that accepts `.xlsx`
- **THEN** the dropzone shows `ceda.xlsx` with its size, and reports the file to its owner

#### Scenario: The wrong kind of file

- **WHEN** a user drops `invoice.pdf` onto a dropzone that accepts `.xlsx`
- **THEN** the dropzone says `invoice.pdf` isn't an accepted file, and reports no file
