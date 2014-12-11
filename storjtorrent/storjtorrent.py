#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The MIT License (MIT)
#
# Copyright (c) 2014 Josh Brandoff
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from .exception import StorjTorrentError
import libtorrent as lt
import os
import sys


class StorjTorrent(object):

    """Python libtorrent abstraction interface for Storj nodes."""

    def __init__(self):
        """Initialize StorjTorrent with supplied settings."""
        pass

    @staticmethod
    def generate_torrent(self, shard_directory, piece_size=0,
                         pad_size_limit=4 * 1024 * 1024, flags=1,
                         comment='Storj - Be the Cloud.', creator='Storj',
                         private=False, bootstrap_node='router.bittorrent.com',
                         bootstrap_port=6881, torrent_name='storj.torrent',
                         verbose=False):
        """Creates a torrent with specified files.

        A torrent is created by determining the files that will be included,
        defining the torrent properties (such as DHT nodes), reading through
        all the torrent files, SHA-1ing all the data, setting the piece hashes
        and bencoding the torrent into a file.

        :param piece_size: The size of each piece in bytes. It must be a
                           multiple of 16 kiB. If a piece size of 0 is
                           specified, a piece_size will be calculated such that
                           the torrent file is roughly 40 kB.
        :type piece_size: int
        :param shard_directory: The directory containing the shards you wish to
                                include in the torrent.
        :type shard_directory: str
        :param pad_size_limit: If specified (other than -1), any file larger
                               than the specified number of bytes will be
                               preceeded by a pad file to align it with the
                               start of a peice. The pad_file_limit is ignored
                               unless the optimize flag is passed. Typically it
                               doesn't make sense to set this any lower than
                               4kiB.
        :type pad_size_limit: int
        """

        if piece_size % 16384 is not 0:
            raise StorjTorrentError(
                'Torrent piece size must be 0 or a multiple of 16 kiB.')

        storage = lt.file_storage()
        directory = os.path.abspath(shard_directory)
        parent_directory = os.path.split(directory)[0]

        for root, dirs, files in os.walk(directory):
            if os.path.split(root)[1][0] == '.':
                continue
            for f in files:
                if f[0] in ['.', 'Thumbs.db']:
                    continue
                filename = os.path.join(root[len(parent_directory) + 1:], f)
                size = os.path.getsize(
                    os.path.join(parent_directory, filename))
                if verbose:
                    print '%10d kiB  %s' % (size / 1024, filename)
                storage.add_file(filename, size)

        if storage.num_files() == 0:
            raise StorjTorrentError(
                'No files were loaded from the specified directory.')

        torrent = lt.create_torrent(storage, piece_size, pad_size_limit, flags)
        torrent.set_comment(comment)
        torrent.set_creator(creator)
        torrent.set_priv(private)
        torrent.add_node(bootstrap_node, bootstrap_port)

        if verbose:
            sys.stderr.write('Setting piece hashes.')
            lt.set_piece_hashes(
                torrent, parent_directory, lambda x: sys.stderr.write('.'))
            sys.stderr.write('done!\n')
        else:
            lt.set_piece_hashes(torrent, parent_directory)

        with open(torrent_name, 'wb+') as torrent_file:
            torrent_file.write(lt.bencode(torrent.generate()))
