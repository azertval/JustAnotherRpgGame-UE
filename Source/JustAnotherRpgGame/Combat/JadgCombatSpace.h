// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Combat/CombatSpace.h"

#include <optional>
#include <vector>

#include "CoreMinimal.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/WeakObjectPtr.h"
#include "UObject/WeakObjectPtrTemplates.h"

class AActor;
class AJadgMapFrame;
class UEnvQuery;
class UWorld;

/// Ce qu'a coûté la dernière requête de candidats : ce que la fiche du LOT-1017 relève.
struct FJadgCandidateStats
{
	/// Les points que l'EQS a rendus, projetés sur le maillage de navigation.
	int32 Generated = 0;
	/// Ceux qui sont restés : place libre, chemin dans le budget.
	int32 Kept = 0;
	/// Vrai si les points venaient de l'EQS ; faux s'il a fallu l'échantillonnage de secours.
	bool bFromEqs = false;
	double Milliseconds = 0.0;
};

/// Ce qu'ont coûté toutes les requêtes de candidats d'un espace, les sans-limite à part.
struct FJadgCandidateTotals
{
	int32 Queries = 0;
	int32 EqsQueries = 0;
	int64 Generated = 0;
	int64 Kept = 0;
	double Milliseconds = 0.0;
	double WorstMilliseconds = 0.0;
	int32 UnlimitedQueries = 0;
	double UnlimitedMilliseconds = 0.0;
	double WorstUnlimitedMilliseconds = 0.0;
};

/**
 * @brief L'espace de combat du moteur (`core::CombatSpace`, LOT-1017) : le maillage de navigation
 *        pour les chemins et les budgets, les rayons pour la vue et le sol, un balayage pour la
 *        place libre, l'EQS pour les places candidates.
 *
 * Les mètres de Core se rapportent au repère de la carte (`AJadgMapFrame` : le coin de la case
 * (0, 0), l'est et le sud), décalé de @p OriginCells : une session de combat joue sur la carte
 * réduite à sa zone (`core::cropLevelToZone`), dont la case (0, 0) est le coin de la zone. La
 * hauteur est celle du monde au-dessus du repère. Les règles ne voient que l'interface : ce qui
 * vient du moteur est ici, et nulle part ailleurs dans Core.
 *
 * **Les candidats** (sous-lot 2) : une requête de l'Environment Query System **construite en
 * C++** — aucun asset —, une grille (`UEnvQueryGenerator_SimpleGrid`) d'un pas d'une demi-case
 * (0,75 m) autour du mobile, projetée sur le maillage de navigation. Sa demi-largeur est le budget ;
 * un budget **sans limite** (négatif, l'approche de l'IA) prend tout le maillage de navigation de
 * la carte. Chaque point est ensuite gardé s'il est une place libre (`isClear`, aucun volume de la
 * requête recouvert) et si le maillage y trouve un chemin dans le budget : ce chemin est celui que
 * la `core::Destination` rend. Sans gestionnaire d'EQS (un monde sans système d'IA), la même grille
 * s'échantillonne en C++, et `LastStats` le dit.
 *
 * Ce que le moteur ne sait pas encore faire : exclure un volume (un ennemi) du maillage le temps
 * d'une requête. Les volumes `blocking` d'une requête ne sont donc pris en compte qu'à l'arrivée
 * (on ne finit pas dessus), pas sur le trajet.
 */
class FJadgCombatSpace final : public core::CombatSpace
{
public:
	FJadgCombatSpace(UWorld* InWorld, const AJadgMapFrame* InFrame, FVector2D InOriginCells = FVector2D::ZeroVector);
	virtual ~FJadgCombatSpace() override;

	/// Le point du monde d'un point de Core.
	[[nodiscard]] FVector ToWorld(core::Meters3 Point) const;
	/// Le point de Core d'un point du monde.
	[[nodiscard]] core::Meters3 FromWorld(const FVector& Point) const;

	[[nodiscard]] float groundHeight(float X, float Y) const override;
	[[nodiscard]] bool isClear(const core::Volume& Volume, core::Locomotion Locomotion) const override;
	[[nodiscard]] bool lineOfSight(core::Meters3 From, core::Meters3 To) const override;
	[[nodiscard]] std::optional<core::Route> route(const core::RouteQuery& Query) const override;
	[[nodiscard]] std::vector<core::Destination> candidates(const core::RouteQuery& Query) const override;

	/// Ce qu'a coûté la dernière requête de candidats.
	const FJadgCandidateStats& LastStats() const { return Stats; }
	/// Ce qu'ont coûté toutes les requêtes de candidats depuis la création de l'espace.
	const FJadgCandidateTotals& Totals() const { return Sum; }

	/// Le pas de la grille des candidats, en mètres : une demi-case.
	static constexpr float CandidateStep = 0.75f;

private:
	[[nodiscard]] bool OverlapsBlocking(core::Meters3 Point, const core::RouteQuery& Query) const;
	/// La demi-largeur de la grille d'une requête, en mètres : le budget, ou tout le maillage.
	[[nodiscard]] float GridHalfWidth(const core::RouteQuery& Query) const;
	/// Les points de la grille, projetés sur le maillage : par l'EQS, ou par l'échantillonnage de secours.
	[[nodiscard]] TArray<FVector> GridPoints(const core::RouteQuery& Query, float HalfWidth) const;
	[[nodiscard]] UEnvQuery* QueryFor(float HalfWidth) const;

	UWorld* World;
	const AJadgMapFrame* Frame;
	FVector2D OriginCells;
	mutable FJadgCandidateStats Stats;
	mutable FJadgCandidateTotals Sum;
	/// L'acteur dont l'EQS prend la place : le mobile n'est pas un acteur pour Core.
	mutable TWeakObjectPtr<AActor> Querier;
	/// Les requêtes construites, par demi-largeur en centimètres : le gestionnaire d'EQS garde une
	/// copie de chaque requête par son nom, une requête ne se réutilise donc qu'à paramètres égaux.
	mutable TMap<int32, TStrongObjectPtr<UEnvQuery>> Queries;
};
