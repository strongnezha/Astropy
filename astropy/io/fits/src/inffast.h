/* $Id$
*/

/*****************************************************************************/
/*                                                                           */
/* This file, zlib.h, contains the include information required to compress  */
/* and uncompress data using the GZIP_1 compression format.                  */
/*                                                                           */
/* Copyright (C) 2004 Association of Universities for Research in Astronomy  */
/* (AURA)                                                                    */
/*                                                                           */
/* Redistribution and use in source and binary forms, with or without        */
/* modification, are permitted provided that the following conditions are    */
/* met:                                                                      */
/*                                                                           */
/*    1. Redistributions of source code must retain the above copyright      */
/*      notice, this list of conditions and the following disclaimer.        */
/*                                                                           */
/*    2. Redistributions in binary form must reproduce the above             */
/*      copyright notice, this list of conditions and the following          */
/*      disclaimer in the documentation and/or other materials provided      */
/*      with the distribution.                                               */
/*                                                                           */
/*    3. The name of AURA and its representatives may not be used to         */
/*      endorse or promote products derived from this software without       */
/*      specific prior written permission.                                   */
/*                                                                           */
/* THIS SOFTWARE IS PROVIDED BY AURA ``AS IS'' AND ANY EXPRESS OR IMPLIED    */
/* WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF      */
/* MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE                  */
/* DISCLAIMED. IN NO EVENT SHALL AURA BE LIABLE FOR ANY DIRECT, INDIRECT,    */
/* INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,      */
/* BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS     */
/* OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND    */
/* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR     */
/* TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE    */
/* USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH          */
/* DAMAGE.                                                                   */
/*                                                                           */
/* This code was copied and heavily modified from the ZLIB compression       */
/* library that was written by Jean-loup Gailly and Mark Adler.  That        */
/* software containes the following copyright and warranty notices:          */
/*                                                                           */
/*  Copyright (C) 1995-2010 Jean-loup Gailly and Mark Adler                  */
/*                                                                           */
/*  This software is provided 'as-is', without any express or implied        */
/*  warranty.  In no event will the authors be held liable for any damages   */
/*  arising from the use of this software.                                   */
/*                                                                           */
/*  Permission is granted to anyone to use this software for any purpose,    */
/*  including commercial applications, and to alter it and redistribute it   */
/*  freely, subject to the following restrictions:                           */
/*                                                                           */
/*  1. The origin of this software must not be misrepresented; you must not  */
/*     claim that you wrote the original software. If you use this software  */
/*     in a product, an acknowledgment in the product documentation would be */
/*     appreciated but is not required.                                      */
/*  2. Altered source versions must be plainly marked as such, and must not  */
/*     be misrepresented as being the original software.                     */
/*  3. This notice may not be removed or altered from any source             */
/*     distribution.                                                         */
/*                                                                           */
/*  Jean-loup Gailly        Mark Adler                                       */
/*  jloup@gzip.org          madler@alumni.caltech.edu                        */
/*                                                                           */
/*                                                                           */
/*                                                                           */
/*  The data format used by the zlib library is described by RFCs (Request   */
/*  for Comments) 1950 to 1952 in the files                                  */
/*  http://www.ietf.org/rfc/rfc1950.txt (zlib format),                       */
/*  rfc1951.txt (deflate format) and rfc1952.txt (gzip format).              */
/*                                                                           */
/*****************************************************************************/

/* This code was copied unmodified from ZLIB inffast.h                       */

void ZLIB_INTERNAL inflate_fast OF((z_streamp strm, unsigned start));
