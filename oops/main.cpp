
#include "models.h"

#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <unordered_map>
#include <vector>
#include <string>
#include <memory>
#include <cctype>
#include <stdexcept>
#include <utility>

using namespace std;

// ==========================================
// DATASET DIRECTORY
// ==========================================

const vector<string> DATA_DIRS = {
    "shared data/data/processed/",
    "../shared data/data/processed/",
    "../../shared data/data/processed/"
};

// ==========================================
// FIND DATA FILE
// ==========================================

string findDataFile(const string& filename) {

    for (const string& directory : DATA_DIRS) {

        string path = directory + filename;

        ifstream file(path);

        if (file.is_open()) {
            return path;
        }
    }

    throw runtime_error(
        "Could not find dataset: " + filename +
        "\nCheck your shared data/data/processed folder."
    );
}

// ==========================================
// CSV PARSER
// ==========================================

vector<string> parseCSVLine(const string& line) {

    vector<string> fields;
    string field;

    bool insideQuotes = false;

    for (size_t i = 0; i < line.size(); i++) {

        char ch = line[i];

        if (ch == '"') {

            if (insideQuotes &&
                i + 1 < line.size() &&
                line[i + 1] == '"') {

                field += '"';
                i++;

            } else {

                insideQuotes = !insideQuotes;
            }

        } else if (ch == ',' && !insideQuotes) {

            fields.push_back(field);
            field.clear();

        } else {

            field += ch;
        }
    }

    fields.push_back(field);

    return fields;
}

// ==========================================
// DATASET STRUCTURE
// ==========================================

struct Dataset {

    vector<unordered_map<string, string>> artworks;

    vector<unordered_map<string, string>> provenance;
};

// ==========================================
// LOAD CSV FILE
// ==========================================

vector<unordered_map<string, string>>
loadCSV(const string& filename) {

    string path = findDataFile(filename);

    ifstream file(path);

    if (!file.is_open()) {
        throw runtime_error("Unable to open file: " + path);
    }

    string line;

    if (!getline(file, line)) {
        throw runtime_error("Dataset is empty: " + filename);
    }

    if (!line.empty() && line.back() == '\r') {
        line.pop_back();
    }

    vector<string> headers = parseCSVLine(line);

    if (!headers.empty() &&
        headers[0].size() >= 3 &&
        static_cast<unsigned char>(headers[0][0]) == 0xEF &&
        static_cast<unsigned char>(headers[0][1]) == 0xBB &&
        static_cast<unsigned char>(headers[0][2]) == 0xBF) {

        headers[0].erase(0, 3);
    }

    vector<unordered_map<string, string>> records;

    while (getline(file, line)) {

        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }

        if (line.empty()) {
            continue;
        }

        vector<string> values = parseCSVLine(line);

        unordered_map<string, string> record;

        for (size_t i = 0; i < headers.size(); i++) {

            record[headers[i]] =
                (i < values.size() ? values[i] : "");
        }

        records.push_back(move(record));
    }

    return records;
}

// ==========================================
// LOAD BOTH DATASETS
// ==========================================

Dataset loadDatasets() {

    cout << "\nLoading datasets...\n";

    Dataset data;

    data.artworks = loadCSV("artworks.csv");

    data.provenance = loadCSV("provenance_statements.csv");

    cout << "Total artworks: "
         << data.artworks.size() << '\n';

    cout << "Total statements: "
         << data.provenance.size() << '\n';

    cout << "\nDATASETS LOADED SUCCESSFULLY\n";

    return data;
}

// ==========================================
// CLEAN TEXT
// ==========================================

string clean(const string& value) {

    size_t start =
        value.find_first_not_of(" \t\r\n");

    if (start == string::npos) {
        return "";
    }

    size_t end =
        value.find_last_not_of(" \t\r\n");

    return value.substr(start, end - start + 1);
}

// ==========================================
// GET CSV VALUE
// ==========================================

string getValue(
    const unordered_map<string, string>& row,
    const string& column
) {

    auto it = row.find(column);

    if (it == row.end()) {
        throw runtime_error("Missing CSV column: " + column);
    }

    return clean(it->second);
}

// ==========================================
// CONVERT TEXT TO LOWERCASE
// ==========================================

string toLower(string text) {

    transform(
        text.begin(),
        text.end(),
        text.begin(),
        [](unsigned char ch) {
            return static_cast<char>(tolower(ch));
        }
    );

    return text;
}

// ==========================================
// CREATE ARTWORK OBJECT
// ==========================================

Artwork createArtwork(
    const unordered_map<string, string>& row
) {

    return Artwork(
        getValue(row, "artwork_id"),
        getValue(row, "title"),
        getValue(row, "artist"),
        getValue(row, "owner"),
        getValue(row, "medium"),
        getValue(row, "description")
    );
}

// ==========================================
// CREATE PROVENANCE STATEMENT OBJECT
// ==========================================

unique_ptr<ProvenanceStatement> createStatement(
    const unordered_map<string, string>& row
) {

    string statementId =
        getValue(row, "statement_id");

    string artworkId =
        getValue(row, "artwork_id");

    string statementType =
        getValue(row, "statement_type");

    string value =
        getValue(row, "statement_value_raw");

    string date =
        getValue(row, "normalized_date");

    string sourceName =
        getValue(row, "source_name");

    string dateStatus =
        getValue(row, "date_status");

    string type = toLower(statementType);

    if (type == "intake place" ||
        type == "transfer place") {

        return make_unique<PlaceStatement>(
            statementId, artworkId, statementType,
            value, date, sourceName, dateStatus
        );
    }

    if (type == "intake date" ||
        type == "transfer date") {

        return make_unique<DateStatement>(
            statementId, artworkId, statementType,
            value, date, sourceName, dateStatus
        );
    }

    return make_unique<GeneralStatement>(
        statementId, artworkId, statementType,
        value, date, sourceName, dateStatus
    );
}

// ==========================================
// INVESTIGATE AN ARTWORK
// ==========================================

void investigateArtwork(
    const Dataset& data,
    const string& targetId
) {

    auto artworkIt = find_if(
        data.artworks.begin(),
        data.artworks.end(),
        [&](const auto& row) {
            return getValue(row, "artwork_id") == targetId;
        }
    );

    if (artworkIt == data.artworks.end()) {

        cout << "\nArtwork not found: "
             << targetId << '\n';

        return;
    }

    Artwork artwork = createArtwork(*artworkIt);

    ProvenanceRecord record(artwork);

    int placeCount = 0;
    int dateCount = 0;
    int generalCount = 0;

    for (const auto& row : data.provenance) {

        if (getValue(row, "artwork_id") == targetId) {

            unique_ptr<ProvenanceStatement> statement =
                createStatement(row);

            if (dynamic_cast<PlaceStatement*>(statement.get())) {
                placeCount++;
            } else if (
                dynamic_cast<DateStatement*>(statement.get())
            ) {
                dateCount++;
            } else {
                generalCount++;
            }

            record.addStatement(move(statement));
        }
    }

    artwork.display();

    cout << "\nSTATEMENT CLASSIFICATION\n";
    cout << "========================\n";

    cout << "Place Statements: " << placeCount << '\n';
    cout << "Date Statements: " << dateCount << '\n';
    cout << "General Statements: " << generalCount << '\n';

    record.showHistory();
    record.showDetailedHistory();
}

// ==========================================
// SEARCH BY ARTWORK ID
// ==========================================

void searchById(const Dataset& data) {

    string id;

    cout << "\nEnter Artwork ID: ";
    getline(cin, id);

    id = clean(id);

    if (id.empty()) {
        cout << "Please enter a valid Artwork ID.\n";
        return;
    }

    investigateArtwork(data, id);
}

// ==========================================
// SEARCH BY ARTWORK TITLE
// ==========================================

void searchByTitle(const Dataset& data) {

    string title;

    cout << "\nEnter artwork title or keyword: ";
    getline(cin, title);

    title = toLower(clean(title));

    if (title.empty()) {
        cout << "Please enter a title or keyword.\n";
        return;
    }

    int matches = 0;

    cout << "\nSEARCH RESULTS\n";
    cout << "==============\n";

    for (const auto& row : data.artworks) {

        string artworkTitle = getValue(row, "title");

        if (toLower(artworkTitle).find(title) != string::npos) {

            cout << ++matches << ". "
                 << getValue(row, "artwork_id")
                 << " | " << artworkTitle << '\n';
        }
    }

    if (matches == 0) {
        cout << "No matching artworks found.\n";
        return;
    }

    cout << "\nEnter the Artwork ID from the results: ";

    string id;
    getline(cin, id);

    investigateArtwork(data, clean(id));
}

// ==========================================
// SEARCH BY ARTIST NAME
// ==========================================

void searchByArtist(const Dataset& data) {

    string artist;

    cout << "\nEnter artist name or keyword: ";
    getline(cin, artist);

    artist = toLower(clean(artist));

    if (artist.empty()) {
        cout << "Please enter an artist name.\n";
        return;
    }

    int matches = 0;

    cout << "\nARTIST SEARCH RESULTS\n";
    cout << "=====================\n";

    for (const auto& row : data.artworks) {

        string artistName = getValue(row, "artist");

        if (toLower(artistName).find(artist) != string::npos) {

            cout << ++matches << ". "
                 << getValue(row, "artwork_id")
                 << " | " << getValue(row, "title")
                 << " | Artist: " << artistName << '\n';
        }
    }

    if (matches == 0) {
        cout << "No artworks found for this artist.\n";
    }
}

// ==========================================
// DATASET STATISTICS
// ==========================================

void showStatistics(const Dataset& data) {

    int placeCount = 0;
    int dateCount = 0;
    int generalCount = 0;

    for (const auto& row : data.provenance) {

        string type = toLower(
            getValue(row, "statement_type")
        );

        if (type == "intake place" ||
            type == "transfer place") {

            placeCount++;

        } else if (
            type == "intake date" ||
            type == "transfer date"
        ) {

            dateCount++;

        } else {

            generalCount++;
        }
    }

    cout << "\n====================================\n";
    cout << "          DATASET STATISTICS\n";
    cout << "====================================\n";

    cout << "Total artworks: "
         << data.artworks.size() << '\n';

    cout << "Total provenance statements: "
         << data.provenance.size() << '\n';

    cout << "\nSTATEMENT BREAKDOWN\n";
    cout << "-------------------\n";

    cout << "Place statements: " << placeCount << '\n';
    cout << "Date statements: " << dateCount << '\n';
    cout << "General statements: " << generalCount << '\n';

    cout << "\nSTATISTICS DISPLAYED SUCCESSFULLY\n";
}

// ==========================================
// DISPLAY MENU
// ==========================================

void displayMenu() {

    cout << "\n";
    cout << "============================================\n";
    cout << "       NAZI-LOOTED ART PROVENANCE SYSTEM\n";
    cout << "============================================\n";

    cout << "1. Search artwork by ID\n";
    cout << "2. Search artwork by title\n";
    cout << "3. Search artwork by artist\n";
    cout << "4. View dataset statistics\n";
    cout << "5. Exit\n";

    cout << "============================================\n";
    cout << "Enter your choice: ";
}

// ==========================================
// MAIN FUNCTION
// ==========================================

int main() {

    try {

        Dataset data = loadDatasets();

        string choice;

        while (true) {

            displayMenu();

            if (!getline(cin, choice)) {
                break;
            }

            if (choice == "1") {

                searchById(data);

            } else if (choice == "2") {

                searchByTitle(data);

            } else if (choice == "3") {

                searchByArtist(data);

            } else if (choice == "4") {

                showStatistics(data);

            } else if (choice == "5") {

                cout << "\nThank you for using the "
                     << "Provenance System!\n";

                cout << "Exiting program...\n";

                break;

            } else {

                cout << "\nInvalid choice. "
                     << "Please enter a number from 1 to 5.\n";
            }
        }

    } catch (const exception& error) {

        cerr << "\nERROR: " << error.what() << '\n';

        return 1;
    }

    return 0;
}
