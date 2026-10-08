// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Diagnostics/ILogSink.h"
#include "Core/Diagnostics/LogLevel.h"
#include "Core/Diagnostics/Logger.h"

#include <memory>
#include <string>
#include <string_view>

#include "Bridge/JadgLog.h"
#include "JustAnotherRpgGame.h"

namespace
{
	class FUnrealLogSink final : public core::ILogSink
	{
	public:
		void write(core::LogLevel Level, std::string_view Message) override
		{
			const FString Line(UTF8_TO_TCHAR(std::string(Message).c_str()));
			switch (Level)
			{
			case core::LogLevel::Error:
				UE_LOG(LogJadg, Error, TEXT("%s"), *Line);
				break;
			case core::LogLevel::Warning:
				UE_LOG(LogJadg, Warning, TEXT("%s"), *Line);
				break;
			case core::LogLevel::Info:
				UE_LOG(LogJadg, Log, TEXT("%s"), *Line);
				break;
			default:
				UE_LOG(LogJadg, Verbose, TEXT("%s"), *Line);
				break;
			}
		}
	};

	bool bInstalled = false;
}

void FJadgCoreLogBridge::Install()
{
	if (bInstalled)
	{
		return;
	}
	core::defaultLogger().addSink(std::make_unique<FUnrealLogSink>());
	bInstalled = true;
}

void FJadgCoreLogBridge::Uninstall()
{
	if (!bInstalled)
	{
		return;
	}
	core::defaultLogger().clearSinks();
	bInstalled = false;
}
