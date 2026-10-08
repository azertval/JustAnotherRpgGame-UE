// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Diagnostics/FileLogSink.h"

#include <system_error>

namespace core {

FileLogSink::FileLogSink(const std::filesystem::path& path, bool append) {
    // Cree les dossiers parents au besoin ; ignore silencieusement une erreur (ex. chemin deja
    // existant ou droits insuffisants) et laisse l'ouverture du flux ci-dessous echouer/reussir
    // pour son propre compte -- journaliser ne doit jamais faire echouer l'appelant.
    const std::filesystem::path parent = path.parent_path();
    if (!parent.empty()) {
        std::error_code errorCode;
        std::filesystem::create_directories(parent, errorCode);
    }

    const std::ios_base::openmode mode = std::ios::out | (append ? std::ios::app : std::ios::trunc);
    _stream.open(path, mode);
}

// Ecrit une ligne deja formatee (horodatage/niveau/categorie/fichier:ligne, voir LogFormat.h) et
// flush immediatement : voir le commentaire de classe sur la garantie apres un arret brutal.
void FileLogSink::write(LogLevel level, std::string_view message) {
    (void)level;  // Deja encode dans la ligne formatee, rien a filtrer/dispatcher ici.
    if (!_stream.is_open()) {
        return;
    }
    _stream << message << '\n';
    _stream.flush();
}

bool FileLogSink::isOpen() const {
    return _stream.is_open();
}

}  // namespace core
