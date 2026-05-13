/*
Copyright (C) 2017  Liangliang Nan
https://3d.bk.tudelft.nl/liangliang/ - liangliang.nan@gmail.com

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

#include <QApplication>
#include <QTimer>
#include <iostream>
#include <QLocale>
#include <QDebug>
#include <QSurfaceFormat>
#include "main_window.h"
#include <time.h>

int main(int argc, char **argv)
{
	srand(time(0));

	QLocale locale = QLocale(QLocale::English);
	locale.setNumberOptions(QLocale::c().numberOptions());
	QLocale::setDefault(locale);

#ifdef Q_OS_UNIX
	setlocale(LC_NUMERIC, "C");
#endif

#if (QT_VERSION >= QT_VERSION_CHECK(5, 6, 0) && (QT_VERSION < QT_VERSION_CHECK(6, 0, 0)))
    QApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
#endif

    QSurfaceFormat format = QSurfaceFormat::defaultFormat();
    format.setVersion(4, 3);
    format.setProfile(QSurfaceFormat::CompatibilityProfile);
    format.setDepthBufferSize(24);
    format.setStencilBufferSize(8);
    format.setSwapBehavior(QSurfaceFormat::DoubleBuffer);
    format.setSamples(4);
#ifndef NDEBUG
    format.setOption(QSurfaceFormat::DebugContext);
#endif
    QSurfaceFormat::setDefaultFormat(format);

    QApplication app(argc, argv);
	MainWindow window;	
	window.show();

	// -------------------------------------------------------
	// HEADLESS MODE
	// Usage: City3D.exe <pointcloud> <footprint> <output>
	// Kalau ada 3 argumen, jalankan pipeline tanpa GUI interaction
	// -------------------------------------------------------
	if (argc == 4) {
		QString pcPath  = QString::fromLocal8Bit(argv[1]);
		QString fpPath  = QString::fromLocal8Bit(argv[2]);
		QString outPath = QString::fromLocal8Bit(argv[3]);

		// Pakai QTimer supaya GUI sempat initialize dulu sebelum pipeline jalan
		QTimer::singleShot(1000, [&window, pcPath, fpPath, outPath]() {
			window.runHeadless(pcPath, fpPath, outPath);
		});
	}

	return app.exec();
}
