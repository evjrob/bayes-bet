function plot_model_performance(data, target_div) {

    var parent_div = d3.select(target_div);
    var min_width = 350;
    var max_width = 650;
    var div_width = Math.max(min_width, Math.min(max_width, parseInt(parent_div.style("width"))));
  
    var parseDate = d3.timeParse("%Y-%m-%d")

    data.forEach(function(d) {
      d.date = parseDate(d.date);
      d.cum_acc = +d.cum_acc * 100;
      d.rolling_acc = +d.rolling_acc * 100;
      d.cum_ll = +d.cum_ll;
      d.rolling_ll = +d.rolling_ll;
    });
    var margin = {top: 10, right: 60, bottom: 60, left: 60, between: 50};
    var full_width = div_width;
    var full_height = div_width;
    var width = full_width - margin.left - margin.right;
    var height = full_height - margin.top - margin.bottom;
    var radius = 5;
  
    var yAccMin = d3.min(data, function(d){return d3.min([d.cum_acc, d.rolling_acc])}) * 0.95;
    var yAccMax = d3.max(data, function(d){return d3.max([d.cum_acc, d.rolling_acc])}) * 1.05;
    var yLossMin = d3.min(data, function(d){return d3.min([d.cum_ll, d.rolling_ll])}) * 0.95;
    var yLossMax = d3.max(data, function(d){return d3.max([d.cum_ll, d.rolling_ll])}) * 1.05;
  
    var svg = d3.select(target_div)
    .append("svg")
      .attr("width", full_width)
      .attr("height", full_height)
    .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");
  
    // Add X axis
    var xAccScale = d3.scaleTime()
      .range([ 0, width ])
      .domain(d3.extent(data, function(d) { return d.date; }));
    svg.append("g")
      .attr("transform", "translate(0," + (height/2 - margin.between/2 + margin.top) + ")")
      .call(d3.axisBottom(xAccScale)
              .tickFormat(d3.timeFormat("%b-%d"))
              .ticks(d3.timeDay.every(2)));

    // Labels the x axis
    svg.append("text")       
      .attr("y", height/2 + margin.between/2)
      .attr("x", width/2)
      .style("text-anchor", "middle")
      .text("Date")
      .style("font", "14px sans-serif");

    var xLossScale = d3.scaleTime()
      .range([ 0, width ])
      .domain(d3.extent(data, function(d) { return d.date; }));
    svg.append("g")
      .attr("transform", "translate(0," + (height) + ")")
      .call(d3.axisBottom(xLossScale)
              .tickFormat(d3.timeFormat("%b-%d"))
              .ticks(d3.timeDay.every(2)));
  
    // Labels the x axis
    svg.append("text")       
      .attr("y", height + margin.bottom/2)
      .attr("x", width/2)
      .style("text-anchor", "middle")
      .text("Date")
      .style("font", "14px sans-serif");
    
    // Add Y axis
    var yAccScale = d3.scaleLinear()
      .range([ height/2 - margin.between/3, 0 ])
      .domain([yAccMin, yAccMax]);
    svg.append("g")
      .call(d3.axisLeft(yAccScale));

    // Labels for the y axis
    svg.append("text")       
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - 3*margin.left/4)
      .attr("x", 0 - height/4)
      .style("text-anchor", "middle")
      .text("Accuracy (%)")
      .style("font", "14px sans-serif");

    var yLossScale = d3.scaleLinear()
      .range([ height, height/2 + margin.between/2])
      .domain([yLossMin, yLossMax]);
    svg.append("g")
      .call(d3.axisLeft(yLossScale));
  
    // Labels for the y axis
    svg.append("text")       
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - 3*margin.left/4)
      .attr("x", 0 - 3*height/4)
      .style("text-anchor", "middle")
      .text("Log Loss")
      .style("font", "14px sans-serif");
    
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
  
    var dateFormat = d3.timeFormat("%Y-%m-%d");

    // Functions that change the tooltip when the user hovers / moves / leaves a team circle
    var mouseover = function(d) {
      tooltip.style("opacity", 1)
    }
    var mousemove = function(d, metric) {
      var chart_pos = svg.node().getBoundingClientRect();
      var plot_pos = d3.select('#perf-plot').node().getBoundingClientRect();
      var tooltipText = ";"
      if (metric == 'cum_acc') {
        f = d3.format('.2f')
        tooltipText = "<strong>Since Season Start</strong><br>Date: " 
          + dateFormat(d.date) + "<br>Accuracy: " + f(d.cum_acc) + "%";
      } else if (metric == 'rolling_acc') {
        f = d3.format('.2f')
        tooltipText = "<strong>Rolling (14 days)</strong><br>Date: " 
          + dateFormat(d.date) + "<br>Accuracy: " + f(d.rolling_acc) + "%";
      } else if (metric == 'cum_ll') {
        f = d3.format('.5f')
        tooltipText = "<strong>Since Season Start</strong><br>Date: " 
          + dateFormat(d.date) + "<br>Log Loss: " + f(d.cum_ll);
      } else if (metric == 'rolling_ll') {
        f = d3.format('.5f')
        tooltipText = "<strong>Rolling (14 days)</strong><br>Date: " 
          + dateFormat(d.date) + "<br>Log Loss: " + f(d.rolling_ll);
      }
      tooltip
        .html(tooltipText)
        .style("left", (d3.event.clientX - chart_pos.left  - 40) + "px")
        .style("top", (d3.event.clientY - plot_pos.top + 20) + "px")
    }
    var mouseleave = function(d) {
      tooltip.style("opacity", 0)
    }
  
    // Cumulative accuracy line
    var cumAccLine = d3.line()
      .x(d => xAccScale(d.date))
      .y(d => yAccScale(d.cum_acc))
    
    svg.append("path")
      .attr("class", "line")
      .attr("class", "color-secondary-dark")
      .style("fill", "none")
      .style("stroke-width", 2)
      .attr("d", cumAccLine(data));

    svg.selectAll("circles")
      .data(data)
        .enter()
      .append("circle")
      .attr("class", "color-secondary-dark")
      .attr("stroke", "none")
      .attr("cx", function(d) { return xAccScale(d.date) })
      .attr("cy", function(d) { return yAccScale(d.cum_acc) })
      .attr("r", radius)
      .on("mouseover", mouseover)
      .on("mousemove", d => mousemove(d, "cum_acc"))
      .on("mouseleave", mouseleave);

    // Rolling accuracy line
    var rollingAccLine = d3.line()
      .x(d => xAccScale(d.date))
      .y(d => yAccScale(d.rolling_acc))

    svg.append("path")
      .attr("class", "line")
      .attr("class", "color-secondary")
      .style("fill", "none")
      .style("stroke-width", 2)
      .attr("d", rollingAccLine(data));

    svg.selectAll("circles")
      .data(data)
        .enter()
      .append("circle")
      .attr("class", "color-secondary")
      .attr("stroke", "none")
      .attr("cx", function(d) { return xAccScale(d.date) })
      .attr("cy", function(d) { return yAccScale(d.rolling_acc) })
      .attr("r", radius)
      .on("mouseover", mouseover)
      .on("mousemove", d => mousemove(d, "rolling_acc"))
      .on("mouseleave", mouseleave);

    // Cumulative Loss line
    var cumLossLine = d3.line()
      .x(d => xLossScale(d.date))
      .y(d => yLossScale(d.cum_ll))
    
    svg.append("path")
      .attr("class", "line")
      .attr("class", "color-primary-dark")
      .style("fill", "none")
      .style("stroke-width", 2)
      .attr("d", cumLossLine(data));

    svg.selectAll("circles")
      .data(data)
        .enter()
      .append("circle")
      .attr("class", "color-primary-dark")
      .attr("stroke", "none")
      .attr("cx", function(d) { return xLossScale(d.date) })
      .attr("cy", function(d) { return yLossScale(d.cum_ll) })
      .attr("r", radius)
      .on("mouseover", mouseover)
      .on("mousemove", d => mousemove(d, "cum_ll"))
      .on("mouseleave", mouseleave);

    // Rolling Loss line
    var rollingLossLine = d3.line()
      .x(d => xLossScale(d.date))
      .y(d => yLossScale(d.rolling_ll))

    svg.append("path")
      .attr("class", "line")
      .attr("class", "color-primary")
      .style("fill", "none")
      .style("stroke-width", 2)
      .attr("d", rollingLossLine(data));

    svg.selectAll("circles")
      .data(data)
        .enter()
      .append("circle")
      .attr("class", "color-primary")
      .attr("stroke", "none")
      .attr("cx", function(d) { return xLossScale(d.date) })
      .attr("cy", function(d) { return yLossScale(d.rolling_ll) })
      .attr("r", radius)
      .on("mouseover", mouseover)
      .on("mousemove", d => mousemove(d, "rolling_ll"))
      .on("mouseleave", mouseleave);

  };
  