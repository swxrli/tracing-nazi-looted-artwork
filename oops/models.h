
#ifndef MODELS_H
#define MODELS_H

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <stdexcept>

class ProvenanceStatement {
protected:
    std::string statementId;
    std::string artworkId;
    std::string statementType;
    std::string value;
    std::string date;
    std::string sourceName;
    std::string dateStatus;

public:
    ProvenanceStatement(
        std::string statementId,
        std::string artworkId,
        std::string statementType,
        std::string value,
        std::string date,
        std::string sourceName,
        std::string dateStatus
    );

    virtual ~ProvenanceStatement() = default;

    std::string getArtworkId() const;
    std::string getStatementType() const;

    virtual void display() const = 0;
    virtual std::string getDescription() const = 0;
};

class PlaceStatement : public ProvenanceStatement {
public:
    using ProvenanceStatement::ProvenanceStatement;

    void display() const override;
    std::string getDescription() const override;
};

class DateStatement : public ProvenanceStatement {
public:
    using ProvenanceStatement::ProvenanceStatement;

    void display() const override;
    std::string getDescription() const override;
};

class GeneralStatement : public ProvenanceStatement {
public:
    using ProvenanceStatement::ProvenanceStatement;

    void display() const override;
    std::string getDescription() const override;
};

class Artwork {
private:
    std::string artworkId;
    std::string title;
    std::string artist;
    std::string owner;
    std::string medium;
    std::string description;

    std::vector<std::unique_ptr<ProvenanceStatement>>
        provenanceStatements;

public:
    Artwork(
        std::string artworkId,
        std::string title,
        std::string artist,
        std::string owner,
        std::string medium,
        std::string description
    );

    std::string getArtworkId() const;
    std::string getTitle() const;

    void addStatement(
        std::unique_ptr<ProvenanceStatement> statement
    );

    const std::vector<std::unique_ptr<ProvenanceStatement>>&
    getStatements() const;

    void display() const;
};

class ProvenanceRecord {
private:
    Artwork& artwork;

public:
    explicit ProvenanceRecord(Artwork& artwork);

    void addStatement(
        std::unique_ptr<ProvenanceStatement> statement
    );

    void showHistory() const;
    void showDetailedHistory() const;
};

#endif
