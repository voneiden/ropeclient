/**
 GrblMgmr is a frontend application to interface with Grbl via GrblMQTT
 Copyright (C) 2016 Matti Eiden

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

var path = require("path");
var webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const ProgressBarPlugin = require('progress-bar-webpack-plugin');
var Visualizer = require('webpack-visualizer-plugin');

module.exports = {
    context: __dirname,
    entry: [
        './assets/index'
    ],
    devtool: "source-map",
    output: {
        path: path.resolve('bundle/'),
        filename: "[name].js",
        publicPath: '/static/',

    },
    progress: true,
    module: {
        loaders: [
            // we pass the output from babel loader to react-hot loader
            { test: /\.jsx?$/, exclude: /node_modules/, loaders: ['react-hot', 'babel'] },
            { test: /\.scss$/, exclude: /node_modules/, loader:  ExtractTextPlugin.extract('style','css?localIdentName=[path][name]--[local]','sass')}
        ]
    },

    resolve: {
        modulesDirectories: ['node_modules', 'bower_components'],
        extensions: ['', '.js', '.jsx'],
        alias: {
            'react': 'react-lite',
            'react-dom': 'react-lite'
        }
    },

    plugins: [
        new webpack.DefinePlugin({
            'process.env': {
                NODE_ENV: JSON.stringify(process.env.NODE_ENV)
            },
            '__DEVELOPMENT__': false
        }),


        new webpack.optimize.UglifyJsPlugin(
            {
                minimize: true,
                comments: false,
                sourceMap: true
            }
        ),
        new webpack.optimize.DedupePlugin(),
        new webpack.optimize.OccurrenceOrderPlugin(),
        new Visualizer(),
        new BundleTracker({filename: 'webpack-stats-production.json'}),
        new ExtractTextPlugin("[name].css"),
        new ProgressBarPlugin()
    ]
};