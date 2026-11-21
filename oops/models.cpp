
#include "models.h"

#include <utility>

using namespace std;

// ==========================================
// PROVENANCE STATEMENT
// ==========================================

ProvenanceStatement::ProvenanceStatement(
    string statementId,
    string artworkId,
    string statementType,
    string value,
    string date,
    string sourceName,
    string dateStatus
)
    : statementId(move(statementId)),
      artworkId(move(artworkId)),
      statementType(move(statementType)),
      value(move(value)),
      date(move(date)),
      sourceName(move(sourceName)),
      dateStatus(move(dateStatus)) {}

string ProvenanceStatement::getArtworkId() const {
    return artworkId;
}

string ProvenanceStatement::getStatementType() const {
    return statementType;
}

// ==========================================
// PLACE STATEMENT
// ==========================================

void PlaceStatement::display() const {
    cout << "Statement ID: " << statementId << '\n';
    cout << "Type: " << statementType << '\n';
    cout << "Value: " << value << '\n';
    cout << "Source: " << sourceName << '\n';
}

string PlaceStatement::getDescription() const {
    return "Location recorded: " + value;
}

// ==========================================
// DATE STATEMENT
// ==========================================

void DateStatement::display() const {
    cout << "Statement ID: " << statementId << '\n';
    cout << "Type: " << statementType << '\n';
    cout << "Normalized Date: " << date << '\n';
    cout << "Date Status: " << dateStatus << '\n';
    cout << "Source: " << sourceName << '\n';
}

string DateStatement::getDescription() const {
    return "Recorded date: " + date +
           " (" + dateStatus + ")";
}

// ==========================================
// GENERAL STATEMENT
// ==========================================

void GeneralStatement::display() const {
    cout << "Statement ID: " << statementId << '\n';
    cout << "Type: " << statementType << '\n';
    cout << "Value: " << value << '\n';
    cout << "Source: " << sourceName << '\n';
}

string GeneralStatement::getDescription() const {
    return statementType + ": " + value;
}

// ==========================================
// ARTWORK
// ==========================================

Artwork::Artwork(
    string artworkId,
    string title,
    string artist,
    string owner,
    string medium,
    string description
)
    : artworkId(move(artworkId)),
      title(move(title)),
      artist(move(artist)),
      owner(move(owner)),
      medium(move(medium)),
      description(move(description)) {}

string Artwork::getArtworkId() const {
    return artworkId;
}

string Artwork::getTitle() const {
    return title;
}

void Artwork::addStatement(
    unique_ptr<ProvenanceStatement> statement
) {
    if (!statement) {
        throw invalid_argument(
            "Statement cannot be null."
        );
    }

    if (statement->getArtworkId() != artworkId) {
        throw invalid_argument(
            "Statement belongs to a different artwork."
        );
    }

    provenanceStatements.push_back(move(statement));
}

const vector<unique_ptr<ProvenanceStatement>>&
Artwork::getStatements() const {
    return provenanceStatements;
}

void Artwork::display() const {
    cout << "\nARTWORK INFORMATION\n";
    cout << "===================\n";

    cout << "Artwork ID: " << artworkId << '\n';
    cout << "Title: " << title << '\n';
    cout << "Artist: " << artist << '\n';
    cout << "Owner: " << owner << '\n';
    cout << "Medium: " << medium << '\n';
    cout << "Description: " << description << '\n';

    cout << "Total Provenance Statements: "
         << provenanceStatements.size() << '\n';
}

// ==========================================
// PROVENANCE RECORD
// ==========================================

ProvenanceRecord::ProvenanceRecord(Artwork& artwork)
    : artwork(artwork) {}

void ProvenanceRecord::addStatement(
    unique_ptr<ProvenanceStatement> statement
) {
    artwork.addStatement(move(statement));
}

void ProvenanceRecord::showHistory() const {
    cout << "\nPROVENANCE HISTORY\n";
    cout << "==================\n";

    const auto& statements = artwork.getStatements();

    if (statements.empty()) {
        cout << "No provenance statements available.\n";
        return;
    }

    int number = 1;

    for (const auto& statement : statements) {
        cout << number++ << ". "
             << statement->getDescription() << '\n';
    }
}

void ProvenanceRecord::showDetailedHistory() const {
    cout << "\nDETAILED PROVENANCE HISTORY\n";
    cout << "===========================\n";

    const auto& statements = artwork.getStatements();

    for (const auto& statement : statements) {
        statement->display();
        cout << "---------------------------\n";
    }
}
