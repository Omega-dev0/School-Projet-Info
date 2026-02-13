# Fonctionnalités

## SELECT avec jointure sur trois tables

> une fonctionnalité qui affiche le contenu d’une requête de sélection (SELECT) avec jointure
> sur trois tables ;

```sql
    SELECT reservation.id, reservation.nb_places, place.type_place, place.prix, representation.date, representation.heure, spectacle.libelle, place.id, representation.id
    FROM reservation, place, representation, spectacle
    WHERE reservation.id_client = ?
    AND reservation.id_place = place.id
    AND place.id_representation = representation.id
    AND representation.id_spectacle = spectacle.id
    ORDER BY representation.date, representation.heure
```

[VoirReservations.py](./Modules/Scripts/Client/VoirReservations.py#L22)

## INSERT INTO

> une fonctionnalité qui se traduit par des requêtes d’ajout (INSERT INTO) dans plusieurs
> tables de la BD ;

[ImporterRepresentation.py](./Modules/Scripts/Gerant/ImporterRepresentation.py#L111)

## GROUP BY

> une fonctionnalité qui se traduit par une requête complexe : soit un GROUP BY, soit deux
> sous-requêtes et l’opérateur ’not in’ ;

```sql
    SELECT spectacle.id, spectacle.libelle, spectacle.site_web, COUNT( distinct   representation.id)
    FROM spectacle,representation
    WHERE spectacle.id = representation.id_spectacle
    AND representation.date >= DATE('now')
    GROUP BY spectacle.id
    ORDER BY spectacle.libelle
```

[AcheterPlace.py](./Modules/Scripts/Client/AcheterPlace.py#L39)

# Scénario de test

- Cree un compte examinteur
- Modifie infos personnels

- Se reinseigner
- Achat place --> Hamilton
  --> Demo mettre de la merde
  --> Demo mettre trop de places
  --> Cat A et Cat D

- Voir ses réservations
- Oublié une place our votre copain Vincent Guigue
  --> Modification reservations

- Voir réservations

--> Vincent pas dispo
--> Annualtion
--> Voir reservation

---

Deconnexion
--> Compte gérant

- Importer une repreésentation
- Se renseugnersur les spectacles

-> Ajouter une représentation
--> Check date (31/02)
--> Ajouter 3 catégories (A/120/45, B/200,36) -> Affiche fur a mesure
-> Elle est bien la

- Tableau de bord
- Voir les réservations de son compte

--> Un retard de 10 minutes sur une représentation
--> Change l'heure
--> + Monte prix
(mentionne que l'on peut ajouter/suppr des catégories)

Suppr représentation maison de poupée
Ajouter leurs spectacle
