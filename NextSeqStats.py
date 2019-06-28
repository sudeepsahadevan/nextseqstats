#!/usr/bin/env python
import argparse
import jinja2
import json
import logging
import os
import re
import sys
import traceback
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from operator import itemgetter

'''
Python module to parser and generate run stats for NextSeq machine
@author: sudeep
Copyright (C) 2017  Sudeep Sahadevan
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
'''

logger = logging.getLogger()

runparam_xpath = {
    'runid':'RunID',
    'rundate':'RunStartDate',
    'basespaceid':'BaseSpaceRunId',
    'runnumber':'RunNumber',
    'read1':'.//Setup/Read1',
    'read2':'.//Setup/Read2',
    'index1':'.//Setup/Index1Read',
    'index2':'.//Setup/Index2Read',
    'libid':'LibraryID',
    'experiment':'ExperimentName'
    }

runcompletion_xpath = {
    'cd':'ClusterDensity',
    'cpf':'ClustersPassingFilter',
    'ey':'EstimatedYield',
    'status':'CompletionStatus'
    }

def plot_d3(all_runs):
    '''
    Return html plots
    '''
    html_template = jinja2.Template('''
    <!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
         <!--
        Copyright (C) 2017  Sudeep Sahadevan
        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.
        
        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>
       -->
      <script type="text/javascript" src="https://d3js.org/d3.v4.js" charset="utf-8"></script>
      <link href='https://fonts.googleapis.com/css?family=Open+Sans' rel='stylesheet' type='text/css'>
        <title>NextSeq 500 run stats</title>
        <style type="text/css">
            head, body {font-family: 'Open Sans', sans-serif;}
            .plotDiv{float: left;}
            #inputf3Label, #inputf5Label{
                color: #cccccc;
            }
            #plotOptions{
                padding-top: 50px;
                padding-bottom: 5px;
            }
            #inputf7Label,#inputf8Label{
                color:#cccccc;
            }
            #divButton1,#divButton2{
                padding-top: 5px;
            }
            .axis{
                font-size: 14px;
            }
         .axis path, .axis line {
             fill: none; 
             stroke: grey; 
             stroke-width: 2; 
             shape-rendering: crispEdges;
         }                
         .line {
             fill: none; 
             stroke-width: 2; 
             opacity: 0.60
         }
         .title{
             font-size: 20px;
             font-weight: bold;
         }
         .label{
             font-size: 16px;
         }
         .description1{
             color: #666666;
         }
         .bar{fill: #0288d1}
         .bar:hover{fill: #4fc3f7}
         .bar2{fill: #388e3c}
         .bar2:hover{fill: #81c784}
         div.tooltip {
             position: absolute;            
                 text-align: center;            
                 width: 30px;                    
                 height: 28px;                    
                 padding: 2px;                
                 font-size: 14px;
                 font-weight: bold;
                 background-color: rgba(0, 0, 0, 0);
                 border: 0px;        
                border-radius: 8px;            
                pointer-events: none;
            }
     </style>
    </head>
    <body>
        <div id="plotElem" class="plotDiv"></div>
        <div id="plotOptions" class="plotDiv">
            <div id="plotOpt1">
                <label for="inputf1" id="inputf1Label"> Select data:<br>
                <select id="inputf1" onchange="updater()" autocomplete="off">
                    <option name="inputOpts" value="count"  selected="selected">Runs per month</option>
                    <option name="inputOpts" value="cd">Avg. Cluster density</option>
                    <option name="inputOpts" value="cpf">Avg. Clusters passing filter</option>
                    <option name="inputOpts" value="ey">Avg. Estimated yield</option>
                </select>            
            </div>
            <div d="plotOpt2">
            <form id="inputf2" autocomplete="off"><br>
                    <input value="line" name="plotChbx1" id="pC1" type="checkbox" onclick="inputActivator()">Plot per month data
            <label for="inputf3" id="inputf3Label"><br>Select year and month:<br>
                <select id="inputf3" autocomplete="off" disabled="disabled">
                    <option name="Yopts" value="16">2016</option>
                    <option name="Yopts" value="17" selected="selected">2017</option>
                    <option name="Yopts" value="18">2018</option>
                </select>
                <select id="inputf4" autocomplete="off"  disabled="disabled">
                <option name="Mopts" value="01" selected="selected">1</option>
                <option name="Mopts" value="02">2</option>
                <option name="Mopts" value="03">3</option>
                <option name="Mopts" value="04">4</option>
                <option name="Mopts" value="05">5</option>
                <option name="Mopts" value="06">6</option>
                <option name="Mopts" value="07">7</option>
                <option name="Mopts" value="08">8</option>
                <option name="Mopts" value="09">9</option>
                <option name="Mopts" value="10">10</option>
                <option name="Mopts" value="11">11</option>
                <option name="Mopts" value="12">12</option>
            </select>
            <label for="inputf5" id="inputf5Label" > <br>Select data:<br>
            <select id="inputf5" autocomplete="off" disabled="disabled">
                <option name="inputOpts5" value="cd"  selected="selected">Cluster density</option>
                <option name="inputOpts5" value="cpf">Clusters passing filter</option>
                <option name="inputOpts5" value="ey">Estimated yield</option>
            </select>
            </div>
            <div id="divButton1">    
                <button id="button1" type="button" onclick="updaterYM()" disabled="disabled">Plot</button> 
            </div>
            <div id="plotOpt3">
                <form id="inputf6" autocomplete="off"><br>
                    <input value="line" name="plotChbx2" id="pC2" type="checkbox" onclick="inputActivator()">Show scatter plots
                <label for="inputf7" id="inputf7Label"><br>Select x axis:<br>
                <select id="inputf7" autocomplete="off" disabled="disabled">
                    <option name="scXopts" value=2>Run number</option>
                    <option name="scXopts" value=3>Read1</option>
                    <option name="scXopts" value=4>Read2</option>
                    <option name="scXopts" value=10 selected="selected">Cluster density</option>
                    <option name="scXopts" value=11>Clusters passing filter</option>
                    <option name="scXopts" value=12>Estimated yield</option>
                </select>
                <label for="inputf8" id="inputf8Label"><br>Select y axis:<br>
                <select id="inputf8" autocomplete="off" disabled="disabled">
                    <option name="scYopts" value=2>Run number</option>
                    <option name="scYopts" value=3>Read1</option>
                    <option name="scYopts" value=4>Read2</option>
                    <option name="scYopts" value=10>Cluster density</option>
                    <option name="scYopts" value=11>Clusters passing filter</option>
                    <option name="scYopts" value=12 selected="selected">Estimated yield</option>
                </select>
            </div>
            <div id="divButton2">    
                <button id="button2" type="button" onclick="updaterScatter()" disabled="disabled">Plot</button> 
            </div>
            <div id="error1"></div>
        </div>
        <script id="data1" type="text/javascript">
        // column names: Date    RunID RunNumber    Read1    Read2    Index1Read    Index2Read    BaseSpaceRunId    ExperimentName    LibraryID    ClusterDensity    ClustersPassingFilter    EstimatedYield    CompletionStatus
            var rundat = {{all_dat_json}};
        </script>
        <script id="functions1" type="text/javascript" >
    
//    
//            source: https://stackoverflow.com/questions/29544371/finding-the-average-of-an-array-using-js
//
            const average = arr => arr.reduce((sume, el) => sume + el, 0) / arr.length;
//            
//            Plot renderer
//
            function plotRender (svg,plotSelector,yLabel) {
                var textArea = document.getElementById('error1');
                textArea.innerHTML="";
                var xScale = d3.scaleBand().rangeRound([0, width]).padding(0.1);
                var yScale = d3.scaleLinear().range([height, 0]);
                var xAxis = d3.axisBottom().scale(xScale);
                xScale.domain(runarr.map(function(d) {return d.date; }));                
                var yAxis = d3.axisLeft().scale(yScale);        
                if (plotSelector=='count') {
                    yScale.domain([0, d3.max(runarr, function(d) {return d.ey.length; })]).nice();
                }else if (plotSelector=='cd') {
                    yScale.domain([0, d3.max(runarr, function(d) {return average(d.cd); })]).nice();
                }else if (plotSelector=='cpf') {
                    yScale.domain([0, d3.max(runarr, function(d) {return average(d.cpf); })]).nice();
                }else if (plotSelector=='ey') {
                    yScale.domain([0, d3.max(runarr, function(d) {return average(d.ey); })]).nice();
                }
//                Define the div for the tooltip
                var div = d3.select("#plotElem").append("div")    
                    .attr("class", "tooltip")                
                    .style("opacity", 0);
//                    X Axis
                svg.append("g")
                    .attr("class", "x axis")
                    .attr("transform", "translate(0," + height + ")")
                    .call(xAxis)
                    .selectAll("text")
                    .attr("y", 0)
                    .attr("x", 9)
                    .attr("dy", ".35em")
                    .attr("transform", "rotate(90)")
                    .style("text-anchor", "start");
//                    Y Axis
                svg.append("g")
                    .attr("class", "y axis")
                    .call(yAxis);
//                Plot
                svg.selectAll(".bar").data(runarr)
                    .enter().append("rect")
                    .attr("class", "bar")
                    .attr("x", function(d) {return xScale(d.date); })
                    .attr("width", xScale.bandwidth())
                    .attr("y", function(d) {
                        if (plotSelector=='count') {return yScale(d.ey.length);}
                        else if (plotSelector=='cd') {return yScale(average(d.cd));}
                        else if (plotSelector=='cpf') {return yScale(average(d.cpf));}
                        else if (plotSelector=='ey') {return yScale(average(d.ey));}
                    })
                    .attr("height", function(d) {
                        if (plotSelector=='count') {return height-yScale(d.ey.length);}
                        else if (plotSelector=='cd') {return height-yScale(average(d.cd));}
                        else if (plotSelector=='cpf') {return height-yScale(average(d.cpf));}
                        else if (plotSelector=='ey') {return height-yScale(average(d.ey));}
                    })
                    .on('mouseover', function (d) {
                        div.transition().duration(200).style("opacity", .9)
                        var hval=0;
                        if (plotSelector=='count') {hval = d.ey.length}
                        else if (plotSelector=='cd') {hval = average(d.cd).toFixed(2)}
                        else if (plotSelector=='cpf') {hval = average(d.cpf).toFixed(2)} 
                        else if (plotSelector=='ey') {hval = average(d.ey).toFixed(2)}
                        div.html(hval).style("left", (d3.event.pageX-28) + "px").style("top", (d3.event.pageY-28) + "px");
                    })                    
                    .on("mouseout", function(d) {
                        div.transition().duration(500).style("opacity", 0);
                        });
//                Add Title
             svg.append("text")
                .attr("class","title")
                .attr("x", titlePosX)
                .attr("y", titlePosY)
                .attr("text-anchor", "middle")
                .text("Nextseq 500 run stats");
//             X Label    
            svg.append("text")
                .attr("class","x label")
                .attr("x", xlabX)
                .attr("y", xlabY)
                .attr("text-anchor", "middle")
               .text('year-month');                
//             Y Label
                svg.append("text")
                    .attr("class","y label")
                    .attr("transform", "rotate(-90)")
                    .attr("y", ylabY)
                    .attr("x",ylabX)
                    .style("text-anchor", "middle")
                    .text(yLabel);                        
            }
//            Per month-year plot renderer
            function plotYMRender(svg,ymdata,plotdata,plotyear,plotmonth,yLabel) {
                var xvals  = [];
                var xScale = d3.scaleBand().rangeRound([0, width]).padding(0.1);
                var yScale = d3.scaleLinear().range([height, 0]);
                for(var i=0;i<ymdata.run1.length;i++){
                    xvals.push(i);
                }
                var yvals = [];
                if (plotdata=='cd') {
                    yvals = ymdata.cd;
                    yScale.domain([0,cdmax]).nice();
                }else if (plotdata=='cpf') {
                    yvals = ymdata.cpf;
                    yScale.domain([0,cpfmax]).nice();
                }else if (plotdata=='ey') {
                    yvals = ymdata.ey;
                    yScale.domain([0,eymax]).nice();
                }
                xScale.domain(xvals);
                var xAxis = d3.axisBottom(xScale)
                    .tickFormat(function(d,i) {return ymdata.run1[i]; });            
                var yAxis = d3.axisLeft().scale(yScale);    
                            
//                Define the div for the tooltip
                var div = d3.select("#plotElem").append("div")    
                    .attr("class", "tooltip")                
                    .style("opacity", 0);
//                    X Axis
                svg.append("g")
                    .attr("class", "x axis")
                    .attr("transform", "translate(0," + height + ")")
                    .call(xAxis)
                    .selectAll("text")
                    .attr("y", 0)
                    .attr("x", 9)
                    .attr("dy", ".35em")
                    .attr("transform", "rotate(90)")
                    .style("text-anchor", "start");
//                    Y Axis
                svg.append("g")
                    .attr("class", "y axis")
                    .call(yAxis);
//                Plot
                svg.selectAll(".bar").data(yvals)
                    .enter().append("rect")
                    .attr("class", "bar2")
                    .attr("x", function (d,i) {return xScale(xvals[i])})
                    .attr("width", xScale.bandwidth())
                    .attr("y", function(d,i) {return yScale(d);})
                    .attr("height", function(d,i) {return height-yScale(d);})
                    .on('mouseover', function (d) {
                        div.transition().duration(200).style("opacity", .9)
                        div.html(d.toFixed(2)).style("left", (d3.event.pageX-28) + "px").style("top", (d3.event.pageY-28) + "px");
                    })                    
                    .on("mouseout", function(d) {
                        div.transition().duration(500).style("opacity", 0);
                        });
//                Add Title
             svg.append("text")
                .attr("class","title")
                .attr("x",titlePosX)
                .attr("y",titlePosY)
                .attr("text-anchor", "middle")
                .text("Nextseq 500 run stats : 20"+plotyear+"."+plotmonth);
//             X Label    
            svg.append("text")
                .attr("class","x label")
                .attr("x", xlabX)
                .attr("y", xlabY)
                .attr("text-anchor", "middle")
               .text("Read length/run");
//             Y Label
                svg.append("text")
                    .attr("class","y label")
                    .attr("transform", "rotate(-90)")
                    .attr("y", ylabY)
                    .attr("x", ylabX)
                    .style("text-anchor", "middle")
                    .text(yLabel);                                                        
            }
//            
//            scatter plotter
//
            function scatterPlotter(svg,onx,ony,xLabel,yLabel) {
                var onxvar = [];
                var onyvar = [];
                for (var i=0;i<rundat.length;i++) {
                    onxvar.push(rundat[i][onx]);
                    onyvar.push(rundat[i][ony]);
                }
                var xlimit = d3.extent(onxvar);
                var ylimit = d3.extent(onyvar);
                var xScale = d3.scaleLinear().domain(xlimit).nice().range([0, width]);
                var yScale = d3.scaleLinear().domain(ylimit).nice().range([height, 0]);
                var xAxis = d3.axisBottom(xScale);
                var yAxis = d3.axisLeft().scale(yScale);
//                push text element messge first
                var textArea = document.getElementById('error1')
                textArea.style.paddingTop="10px";
                textArea.style.fontSize = "12px";
                textArea.style.fontWeight = "bold";
            textArea.style.color = "#000000";
            textArea.innerHTML="Click on a dot for details";
                svg.append("g")
                    .attr("class", "x axis")
                    .attr("transform", "translate(0," + height + ")")
                    .call(xAxis);
                svg.append("g")
                    .attr("class", "y axis")
                .call(yAxis);
                svg.selectAll(".dots").data(onxvar)
                    .enter().append("circle")
                    .attr("class","dots")
                    .attr("r",5)
                    .attr("cx",function (d,i) {return xScale(onxvar[i]);})
                    .attr("cy",function (d,i) {return yScale(onyvar[i]);})
                    .style("fill","rgba(105, 50, 129,0.7)")
                    .on("click",clickEvent)
                    .on("mouseout",mouseOutEvent);
//                Add Title
             svg.append("text")
                .attr("class","title")
                .attr("x", titlePosX)
                .attr("y", titlePosY)
                .attr("text-anchor", "middle")
                .text("Nextseq 500 run stats");
//             X Label    
            svg.append("text")
                .attr("class","x label")
                .attr("x", xlabX)
                .attr("y", xlabY)
                .attr("text-anchor", "middle")
               .text(xLabel);
//             Y Label
                svg.append("text")
                    .attr("class","y label")
                    .attr("transform", "rotate(-90)")
                    .attr("y", ylabY)
                    .attr("x", ylabX)
                    .style("text-anchor", "middle")
                    .text(yLabel);                
//                handle click event
                function clickEvent(d,i) {
                    d3.select(this).transition()
                            .style("fill","#5b2c6f")
                            .attr("r", 8);
//                    textArea.style.fontWeight = "";
                    var dotInfo =rundat[i][8]+"<table id=infoTable><tr><td class=\\"description1\\">Run date</td><td>"+rundat[i][0]+"</td></tr>";
                    dotInfo+="<tr><td class=\\"description1\\">Read1</td><td>"+rundat[i][3]+"</td></tr><tr><td class=\\"description1\\">Read2</td><td>"+rundat[i][4]+"</td></tr>";
                    dotInfo+="<tr><td class=\\"description1\\">BaseSpaceRunId</td><td>"+rundat[i][7]+"</td>";
                    dotInfo+="<tr><td class=\\"description1\\">LibraryID</td><td>"+rundat[i][9]+"</td>";
                    textArea.innerHTML=dotInfo;
                }
//                handle mouse out event
                function mouseOutEvent(d,i) {
                    d3.select(this).transition()
                            .style("fill","rgba(105, 50, 129,0.7)")
                            .attr("r", 5);
                }
            }
            
//        
//            data init and manipulation
// 
            var regx = /\d{2}$/i;
            var runmap = {};
            var cdmax = 0;
            var cpfmax = 0;
            var eymax = 0;
            for (let rn of rundat) {
                rn1 = rn[0].replace(/\d{2}$/i,'');
                if ((rn1 in runmap) && (rn[12]>0)) {
                    runmap[rn1].run1.push(rn[3]);
                    runmap[rn1].run2.push(rn[4]);
                    runmap[rn1].cd.push(rn[10]);
                    runmap[rn1].cpf.push(rn[11]);
                    runmap[rn1].ey.push(rn[12]);
                }else {
                    if (rn[12]>0) {
                        runmap[rn1] = {'date':rn1,'run1':[rn[3]],'run2':[rn[4]],'cd':[rn[10]],'cpf':[rn[11]],'ey':[rn[12]]};
                    }
                }
                if(rn[10]>cdmax){cdmax = rn[10];}
                if(rn[11]>cpfmax){cpfmax = rn[11];}
                if(rn[12]>eymax){eymax = rn[12];}
            }
            var runarr = [];
            for (var key in runmap) {
                runarr.push(runmap[key]);
            }            
//            Plot stuff
            var plotSelector = 'count'
            W1 = 1050;
             H1 = 675;
             var margin = {top: 50, right: 20, bottom: 75, left: 75},
                 width = W1 - margin.left - margin.right,
                 height = H1 - margin.top - margin.bottom;
             var svg = d3.select("#plotElem")
                 .append("svg")
               .attr("height", H1)
               .attr("width", W1)
               .append("g")
               .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
//            define positions for plot labels
            var titlePosX, xlabX;
            titlePosX = xlabX = width/2;
            var titlePosY = 0-(margin.top)/2;
            var xlabY = height+(margin.bottom*0.8);
            var ylabX = 0 - (height / 2);
            var ylabY = 0 - (margin.left*0.6);
//
//            activate and deactivate options
// 
            var cchecker = 0; // variable to store previous state
            function inputActivator() {
                var checker = document.getElementById("pC1").checked;
                var checker2 = document.getElementById("pC2").checked;
//                first plot
                var inputA = document.getElementById('inputf1');
                var inputAlab = document.getElementById('inputf1Label');
//                second plot
                var inputY = document.getElementById('inputf3');
                var inputM = document.getElementById('inputf4');
                var inputYMlab = document.getElementById('inputf3Label');
                var inputO = document.getElementById('inputf5');
                var inputOlab = document.getElementById('inputf5Label');
                var inputB = document.getElementById('button1');
//                third plot
                var inputXX = document.getElementById('inputf7');
                var inputYY = document.getElementById('inputf8');
                var inputXXlab = document.getElementById('inputf7Label');
                var inputYYlab = document.getElementById('inputf8Label');
                var inputB2 = document.getElementById('button2');
                if (checker && checker2 && cchecker==1) { // checker was set before, so disable it 
                    document.getElementById("pC1").checked = false;
                    checker = false;
                }else if (checker && checker2 && cchecker==2) {// checker2 was set before, so disable it
                    document.getElementById("pC2").checked = false;
                    checker2 = false;
                }
                if(checker){
                    cchecker = 1;
                    inputY.disabled = false;
                    inputM.disabled = false;
                    inputO.disabled = false;
                    inputB.disabled = false;
                    inputY.focus();
                    inputM.focus();
                    inputO.focus();
                    inputB.focus();
                    inputYMlab.style.color = '#000000';
                    inputOlab.style.color = '#000000';
//                    disable first plot
                    inputA.disabled = true;
                    inputAlab.style.color = '#cccccc';
//                    disable third plot
                    inputXX.disabled = true;
                    inputYY.disabled = true;
                    inputB2.disabled = true;
                    inputXXlab.style.color = '#cccccc';
                    inputYYlab.style.color = '#cccccc';
                }else if (checker2) {
                    cchecker = 2;
//                    enable third plot
                    inputXX.disabled = false;
                    inputYY.disabled = false;
                    inputB2.disabled = false;
                    inputXXlab.style.color = '#000000';
                    inputYYlab.style.color = '#000000';
//                    disable second plot
                    inputY.disabled = true;
                    inputM.disabled = true;
                    inputYMlab.style.color = '#cccccc';
                    inputO.disabled = true;
                    inputOlab.style.color = '#cccccc';
                    inputB.disabled = true;
//                    disable first plot
                    inputA.disabled = true;
                    inputAlab.style.color = '#cccccc';                                
                }else{
//                    disable second plot
                    inputY.disabled = true;
                    inputM.disabled = true;
                    inputYMlab.style.color = '#cccccc';
                    inputO.disabled = true;
                    inputOlab.style.color = '#cccccc';
                    inputB.disabled = true;
//                    disable third plot
                    inputXX.disabled = true;
                    inputYY.disabled = true;
                    inputB2.disabled = true;
                    inputXXlab.style.color = '#cccccc';
                    inputYYlab.style.color = '#cccccc';                    
//                    enable first plot
                    inputA.disabled = false;
                    inputA.focus();
                    inputAlab.style.color = '#000000';
                    updater();
                }
            }

//            call the  first bar plot on init
//            init y label
            var yLabel = 'Runs per month';
            plotRender(svg,plotSelector,yLabel);
//
//            meta plot renderer
//
            function updater() {
                var plotvar =  document.getElementById("inputf1");
                var plotSelector = plotvar.options[document.getElementById("inputf1").selectedIndex].value;
                yLabel = plotvar.options[document.getElementById("inputf1").selectedIndex].textContent;
                svg.selectAll("g > *").remove();
                plotRender(svg,plotSelector,yLabel);
            }
//
//            plot per month data
//
            function updaterYM() {
                var ploty =  document.getElementById("inputf3");
                var plotyear = ploty.options[document.getElementById("inputf3").selectedIndex].value;
                var plotm =  document.getElementById("inputf4");
                var plotmonth = plotm.options[document.getElementById("inputf4").selectedIndex].value;
                var plotd = document.getElementById("inputf5");
                var plotdata = plotd.options[document.getElementById("inputf5").selectedIndex].value;
                yLabel = plotd.options[document.getElementById("inputf5").selectedIndex].textContent;
                plotym = plotyear+plotmonth;
                var textArea = document.getElementById('error1');
                textArea.contenteditable="true";
            textArea.style.paddingTop="10px";
                if (plotym in runmap) {
                    textArea.innerHTML="";
                    svg.selectAll("g > *").remove();
                    var ymdat = [];
                    ymdat.push(runmap[plotym])
                    plotYMRender(svg,runmap[plotym],plotdata,plotyear,plotmonth,yLabel);
                }else {
                    textArea.style.fontSize = "16px";
                    textArea.style.fontWeight = "bold";
               textArea.style.color = "#ff3300";
               textArea.innerHTML="Error! Cannot find data for period: <font color=\\"#000000\\">20"+plotyear+"."+plotmonth+"</font>";
                }
            }
//            
//            plot scatter plots
//
            function updaterScatter() {
                var xx = document.getElementById("inputf7");
                var xxvar = xx.options[document.getElementById("inputf7").selectedIndex].value;
                var xLabel = xx.options[document.getElementById("inputf7").selectedIndex].textContent;
                var yy = document.getElementById("inputf8");
                var yyvar = xx.options[document.getElementById("inputf8").selectedIndex].value;
                var yLabel = xx.options[document.getElementById("inputf8").selectedIndex].textContent;
                svg.selectAll("g > *").remove();
                scatterPlotter(svg,xxvar,yyvar,xLabel,yLabel);
            }
        </script>
    </body>
</html>
    ''')
    return html_template.render(all_dat_json=json.dumps(all_runs))
    

def parse_run_stats(foldername):
    '''
    Look for illumina run folders in the given parent folder (file name starts with ^\d+\_)
    and if these folders have files named RunParameters.xml and RunCompletionStatus.xml parse'em for info
    '''
    foldername = os.path.abspath(foldername)
    if not os.path.isdir(foldername):
        raise RuntimeError('{} is not a folder!'.format(foldername))
    all_runs = list()
    runs = 0
    for subd in os.listdir(foldername):
        subdf = os.path.join(foldername,subd)
        rp = os.path.join(subdf,'RunParameters.xml')
        rcs = os.path.join(subdf,'RunCompletionStatus.xml')
        if re.match('^\d+\_.*$', subd, re.IGNORECASE):
            if os.path.isdir(subdf) and os.path.exists(rcs) and os.path.exists(rp):
                logging.debug('Run folder : {}'.format(subd))
                run_data = list()
                rpet = ET.parse(rp)
                run_data.append(rpet.find(runparam_xpath['rundate']).text) # date
                run_data.append(rpet.find(runparam_xpath['runid']).text) # run id
                run_data.append(int(rpet.find(runparam_xpath['runnumber']).text)) # run number as int
                run_data.append(int(rpet.find(runparam_xpath['read1']).text)) # read1 as int
                run_data.append(int(rpet.find(runparam_xpath['read2']).text)) # read2 as int
                run_data.append(int(rpet.find(runparam_xpath['index1']).text)) # index1 as int
                run_data.append(int(rpet.find(runparam_xpath['index2']).text)) # index2 as int
                run_data.append(rpet.find(runparam_xpath['basespaceid']).text) # basespacerunid
                run_data.append(rpet.find(runparam_xpath['experiment']).text.encode('ascii', 'ignore')) # Experiment name
                run_data.append(rpet.find(runparam_xpath['libid']).text.encode('ascii', 'ignore')) # Library id
                rcset = ET.parse(rcs)
                run_data.append(float(rcset.find(runcompletion_xpath['cd']).text)) # Cluster density
                run_data.append(float(rcset.find(runcompletion_xpath['cpf']).text)) # Cluster passing filter
                run_data.append(float(rcset.find(runcompletion_xpath['ey']).text)) # Estimated yield
                run_data.append(rcset.find(runcompletion_xpath['status']).text) # status
                all_runs.append(run_data)
                runs+=1
            else:
                logger.warning('Cannot access {}'.format(subd)) 
        else:
            logger.warning('Does not look like an Illumina run folder {}'.format(subd))
    logging.info('Runs parsed: {}'.format(runs))
    return sorted(all_runs,key=itemgetter(0))

def to_csv(all_runs,outname):
    header = ["Date","RunID","RunNumber","Read1","Read2","Index1Read","Index2Read","BaseSpaceRunId","ExperimentName",
              "LibraryID","ClusterDensity","ClustersPassingFilter","EstimatedYield","CompletionStatus"]
    if os.path.exists(outname):
        logging.warning('Over-writing file: {}'.format(outname))
    with open(outname,'w') as oh:
        oh.write("\t".join(header)+"\n")
        for rdat in all_runs:
            oh.write("\t".join(map(lambda rd: str(rd), rdat))+"\n")
    logging.info('TSV data file: {}'.format(outname))

def to_html(all_runs,htmlname):
    if os.path.exists(htmlname):
        logging.warning('Over-writing file: {}'.format(htmlname))
    with open(htmlname,'w') as htmlh:
        htmlh.write(plot_d3(all_runs))
    logging.info('Html plot file: {}'.format(htmlname))

def main(argv):
    prog = re.sub('^.*\/','',argv[0])
    loglevels = ['debug','info','warning','error','quiet']
    description = ''' Generate Nextseq run statistics data.
    NOTE: This script looks for RunParameters.xml and RunCompletionStatus.xml files in all subdirectories of the input folder 
    '''
    epilog = "Example, use: {} --base /illumina/".format(prog)
    ncargs = argparse.ArgumentParser(prog=prog, description=description, epilog=epilog,formatter_class=argparse.RawTextHelpFormatter)
    ncargs.add_argument('--base',metavar='Folder',dest='basefolder',help='Base folder with Illumina runs in subdirectories (example: /illumina/)',required=True)
    ncargs.add_argument('--tsv',metavar='TSV out',dest='tsv',help='Output file name for TSV formatted data, (default: nextseq_run_info.txt)',default='nextseq_run_info.txt', type=str)
    ncargs.add_argument('--html',metavar='HTML out',dest='html',help='Output file name for HTML plots, (default: nextseq_run_info.html)',default='nextseq_run_info.html', type=str)
    ncargs.add_argument('--verbose',metavar='Verbose level',dest='log',help='Allowed choices: '+', '.join(loglevels)+' (default: info)',choices=loglevels,default='info')
    try:
        ncopts = vars(ncargs.parse_args())
        if ncopts['log']== 'quiet':
            logger.addHandler(logging.NullHandler())
        else:
            logger.setLevel(logging.getLevelName(ncopts['log'].upper()))
            consHandle = logging.StreamHandler(sys.stderr)
            consHandle.setLevel(logging.getLevelName(ncopts['log'].upper()))
            consHandle.setFormatter(logging.Formatter(' [%(levelname)s]  %(message)s'))
            logger.addHandler(consHandle)
        all_run_dat = parse_run_stats(ncopts['basefolder'])
        to_csv(all_run_dat, ncopts['tsv'])
        to_html(all_run_dat, ncopts['html'])
    except KeyboardInterrupt:
        sys.stderr.write('Keyboard interrupt...Goodbye\n')
    except Exception:
        traceback.print_exc(file=sys.stdout)
    sys.exit(0)
    
if __name__ == '__main__':
    main(sys.argv)