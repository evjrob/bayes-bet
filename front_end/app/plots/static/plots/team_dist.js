function plot_team_dist(data, target_div) {

  var parent_div = d3.select(target_div);
  var min_width = 350;
  var max_width = 700;
  var div_width = Math.max(min_width, Math.min(max_width, parseInt(parent_div.style("width"))));

  var nodes = [];

  data.forEach(function(d) {
    d.offence_median = +d.offence_median;
    d.offence_hpd_low = +d.offence_hpd_low;
    d.offence_hpd_high = +d.offence_hpd_high;
    d.defence_median = +d.defence_median;
    d.defence_hpd_low = +d.defence_hpd_low;
    d.defence_hpd_high = +d.defence_hpd_high;
  });
  var margin = {top: 10, right: 10, bottom: 60, left: 60};
  var full_width = div_width;
  var full_height = div_width;
  var width = full_width - margin.left - margin.right;
  var height = full_height - margin.top - margin.bottom;
  var radius = 13;

  var x_min = d3.min(data, function(d){return d.defence_median}) * 1.2;
  var x_max = d3.max(data, function(d){return d.defence_median}) * 1.2;
  var y_min = d3.min(data, function(d){return d.offence_median}) * 1.2;
  var y_max = d3.max(data, function(d){return d.offence_median}) * 1.2;

  var svg = d3.select(target_div)
  .append("svg")
    .attr("width", full_width)
    .attr("height", full_height)
  .append("g")
    .attr("transform",
          "translate(" + margin.left + "," + margin.top + ")");

  // Add X axis
  var x = d3.scaleLinear()
    .range([ 0, width ])
    .domain([x_min, x_max]);
  svg.append("g")
    .attr("transform", "translate(0," + (height) + ")")
    .call(d3.axisBottom(x).tickValues([]));

  // Labels for the x axis
  svg.append("text")       
    .attr("y", height + margin.bottom/2)
    .attr("x", width/2)
    .style("text-anchor", "middle")
    .text("Defensive Strength")
    .style("font", "14px sans-serif");
  
  svg.append("text")       
    .attr("y", height + margin.bottom/4)
    .attr("x", 10)
    .style("text-anchor", "starts")
    .text("Weaker")
    .style("font", "10px sans-serif");

  svg.append("text")       
    .attr("y", height + margin.bottom/4)
    .attr("x", width - margin.right)
    .style("text-anchor", "end")
    .text("Stronger")
    .style("font", "10px sans-serif");


  // Add Y axis
  var y = d3.scaleLinear()
    .range([ height, 0 ])
    .domain([y_min, y_max]);
  svg.append("g")
    .call(d3.axisLeft(y).tickValues([]));

  // Labels for the y axis
  svg.append("text")       
    .attr("transform", "rotate(-90)")
    .attr("y", 0 - margin.left/2)
    .attr("x", 0 - height/2)
    .style("text-anchor", "middle")
    .text("Offensive Strength")
    .style("font", "14px sans-serif");
  
  svg.append("text")       
    .attr("transform", "rotate(-90)")
    .attr("y", -5)
    .attr("x", 0 - margin.top)
    .style("text-anchor", "end")
    .text("Stronger")
    .style("font", "10px sans-serif");

  svg.append("text")       
    .attr("transform", "rotate(-90)")
    .attr("y", -5)
    .attr("x", 0 - height + margin.top)
    .style("text-anchor", "start")
    .text("Weaker")
    .style("font", "10px sans-serif");

  data.forEach(function(d) {
    var point_node = {x:x(d.defence_median), 
                      y:y(d.offence_median),
                      offence: d.offence_median,
                      defence: d.defence_median,
                      team_name: d.team_name,
                      team:d.team_abb,
                      team_colors: d.team_colors};
    nodes.push(point_node);
  });


  var force = d3.forceSimulation()
    .nodes(d3.values(nodes))
    .force("collide", d3.forceCollide()
      .strength(1)
      .radius(radius + 1))
    .on("tick", tick);

  // create a tooltip
  var tooltip = d3.select(target_div)
    .append("div")
    .style("opacity", 0)
    .attr("class", "tooltip")
    .style("background-color", "white")
    .style("border", "solid")
    .style("border-width", "2px")
    .style("border-radius", "5px")
    .style("padding", "5px")

  // Functions that change the tooltip when the user hovers / moves / leaves a team circle
  var mouseover = function(d) {
    tooltip.style("opacity", 1)
  }
  var mousemove = function(d) {
    var chart_pos = svg.node().getBoundingClientRect();
    var main_pos = d3.select('#main').node().getBoundingClientRect();
    tooltip
      .html(d.team_name + "<br>Offence: " + d.offence + "<br>Defence: " + d.defence)
      .style("left", (d3.event.clientX - chart_pos.left  - 30) + "px")
      .style("top", (d3.event.clientY - main_pos.top + 80) + "px")
  }
  var mouseleave = function(d) {
    tooltip.style("opacity", 0)
  }

  // define the nodes
  var node = svg.selectAll(".node")
      .data(force.nodes())
    .enter().append("g")
      .attr("class", "node")
    .on("mouseover", mouseover)
    .on("mousemove", mousemove)
    .on("mouseleave", mouseleave);

  // add the nodes
  node.append("circle")
    .attr("r", radius)
    .attr("stroke-width", "2.5px")         
    //.attr("class", "color-primary")
    .attr("fill", function(d) { return d.team_colors[0];})
    .attr("stroke", function(d) { return d.team_colors[1] });

  // add node labels
  node.append("text")
    .style("font-size", "9px")
    .style("fill", "white")
    .style("font-weight", "bold")
    .style("text-anchor", "middle")
    .style("dominant-baseline", "central")
    .text(function(d) { return d.team });

  // add the curvy lines
  function tick() {
    node.attr("transform", function(d) {
      return "translate(" + d.x + "," + d.y + ")"; 
    })
  };
};
