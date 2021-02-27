function plot_goal_dist(data, target_div, home_abb, away_abb) {
    // set the dimensions and margins of the graph
    //var plot_color = document.querySelector('.color-primary').style.fill;

    var parent_div = d3.select(target_div);
    var min_width = 350;
    var max_width = 700;
    var div_width = Math.max(min_width, Math.min(max_width, parseInt(parent_div.style("width"))));

    var full_width = div_width;
    var full_height = div_width;
    var margin = {top: 10, right: 10, bottom: 50, left: 50, between: 10},
    hist_dim = div_width * 0.1,
    width = full_width - margin.left - margin.right - hist_dim - margin.between,
    height = full_height - margin.top - margin.bottom - hist_dim - margin.between;

    // append the svg object to the body of the page
    var svg = d3.select(target_div)
    .append("svg")
    .attr("width", full_width)
    .attr("height", full_height)
    .append("g")
    .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

    // Labels of row and columns
    var home_goal_max = Math.max.apply(Math, data.map(function(d){return d.home_goals;}));
    var away_goal_max = Math.max.apply(Math, data.map(function(d){return d.away_goals;}));
    var goals_range = Array.from(Array(Math.max(home_goal_max, away_goal_max)+1).keys());
    goals_range = goals_range.map(String);

    // Create histogram data
    var axes_data = new Array(goals_range.length);
    for (i=0; i<goals_range.length+1; i++) {
        axes_data[i] = new Object();
        axes_data[i]['goals'] = goals_range[i];
        axes_data[i]['home_probability'] = 0;
        axes_data[i]['away_probability'] = 0;
    }

    // Domain of color range
    var max_probability = Math.max.apply(Math, data.map(function(d){return d.probability;}));

    // Build X scales and axis:
    var x = d3.scaleBand()
        .range([0, width - hist_dim - margin.between])
        .domain(goals_range)
        .padding(0.01);

    // Build X scales and axis:
    var y = d3.scaleBand()
        .range([height, hist_dim + margin.between])
        .domain(goals_range)
        .padding(0.01);
    
    // Build color scale
    var myColor = d3.scaleLinear()
        .range([0, 1])
        .domain([0, max_probability]);

    data.forEach(function(d) {
        d.probability = +d.probability;
        axes_data[d.home_goals]['home_probability'] += d.probability;
        axes_data[d.away_goals]['away_probability'] += d.probability;
        d.home_goals = String(d.home_goals);
        d.away_goals = String(d.away_goals);
    });

    var max_home_prob = Math.max.apply(Math, axes_data.map(function(d){return d.home_probability;}));
    var max_away_prob = Math.max.apply(Math, axes_data.map(function(d){return d.away_probability;}));

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
        .style("position", "absolute")

    // Functions that change the tooltip when the user hovers / moves / leaves a cell
    var mouseover = function(d) {
        tooltip.style("opacity", 1)
    }
    var mousemove_dist = function(d) {
        var chart_pos = svg.node().getBoundingClientRect();
        var main_pos = d3.select('#main').node().getBoundingClientRect();
        tooltip
        .html(home_abb + " goals: " + d.home_goals + "<br>" + away_abb + " goals: " + d.away_goals + "<br>Probability: " + d.probability)
        .style("left", (d3.event.clientX - chart_pos.left  - 30) + "px")
        .style("top", (d3.event.clientY - main_pos.top + 80) + "px")
    }
    var mousemove_home = function(d) {
        var chart_pos = svg.node().getBoundingClientRect();
        var main_pos = d3.select('#main').node().getBoundingClientRect();
        tooltip
        .html(home_abb + " goals: " + d.goals + "<br>Probability: " + Math.round(d.home_probability * 10000)/10000)
        .style("left", (d3.event.clientX - chart_pos.left  - 30) + "px")
        .style("top", (d3.event.clientY - main_pos.top + 80) + "px")
    }
    var mousemove_away = function(d) {
        var chart_pos = svg.node().getBoundingClientRect();
        var main_pos = d3.select('#main').node().getBoundingClientRect();
        tooltip
        .html(away_abb + " goals: " + d.goals + "<br>Probability: " + Math.round(d.away_probability * 10000)/10000)
        .style("left", (d3.event.clientX - chart_pos.left  - 30) + "px")
        .style("top", (d3.event.clientY - main_pos.top + 80) + "px")
    }
    var mouseleave = function(d) {
        tooltip.style("opacity", 0)
    }

    // Add the squares
    svg.selectAll()
        .data(data, function(d) {return d.home_goals+':'+d.away_goals;})
        .enter()
        .append("rect")
        .attr("x", function(d) { return x(d.home_goals) })
        .attr("y", function(d) { return y(d.away_goals) })
        .attr("width", x.bandwidth() )
        .attr("height", y.bandwidth() )
        .attr("class", "color-primary")
        .style("stroke-width", 0)
        .style("opacity", function(d) { return myColor(d.probability)} )
        .on("mouseover", mouseover)
        .on("mousemove", mousemove_dist)
        .on("mouseleave", mouseleave)

    // Top histogram
    var gTop = svg.append("g")
        .attr("transform", "translate(" + 0 + "," + 0 + ")");

    var xTop = d3.scaleBand()
        .range([0, width - hist_dim - margin.between])
        .domain(goals_range);

    svg.append("g")
        .attr("transform", "translate(0," + hist_dim + ")")
        .call(d3.axisBottom(xTop))
        .selectAll("text").remove();

    var xy = d3.scaleLinear()
        .domain(goals_range)
        .range([hist_dim, 0]);

    var xBar = gTop.selectAll(".bar")
        .data(axes_data)
        .enter().append("g")
        .attr("class", "bar")
        .attr("transform", function(d) {
        return "translate(" + x(d.goals) + "," + xy(d.home_probability / max_home_prob) + ")";
        });

    xBar.append("rect")
        .attr("x", 1)
        .attr("width", x.bandwidth())
        .attr("height", function(d) {
        return hist_dim - xy(d.home_probability / max_home_prob);
        })
        .attr("class", "color-primary")
        .style("stroke-width", 0)
        .on("mouseover", mouseover)
        .on("mousemove", mousemove_home)
        .on("mouseleave", mouseleave);

    xBar.append("text")
        .attr("dy", ".75em")
        .attr("y", 2)
        .attr("x", x.bandwidth() / 2)
        .attr("text-anchor", "middle")
        .style("fill", "white")
        .style("font", "9px sans-serif");
        
    // Right histogram
    var gRight = svg.append("g")
        .attr("transform", "translate(" + (width - hist_dim) + ", 0)");

    var yRight = d3.scaleBand()
        .range([height, hist_dim])
        .domain(goals_range);

    svg.append("g")
        .attr("transform", "translate("+ (width - hist_dim) + ", " + 0 + ")")
        .call(d3.axisLeft(yRight))
        .selectAll("text").remove();

    var yx = d3.scaleLinear()
        .domain(goals_range)
        .range([0, hist_dim]);

    var yBar = gRight.selectAll(".bar")
        .data(axes_data)
        .enter().append("g")
        .attr("class", "bar")
        .attr("transform", function(d) {
        return "translate(" + 0 + "," + y(d.goals) + ")";
        });

    yBar.append("rect")
        .attr("y", 1)
        .attr("width", function(d){
        return yx(d.away_probability / max_away_prob);
        })
        .attr("height", y.bandwidth())
        .attr("class", "color-primary")
        .style("stroke-width", 0)
        .on("mouseover", mouseover)
        .on("mousemove", mousemove_away)
        .on("mouseleave", mouseleave);

    yBar.append("text")
        .attr("dx", "-.75em")
        .attr("y", y.bandwidth() / 2 + 1)
        .attr("x", function(d){
        return yx(d.away_probability / max_away_prob);
        })
        .attr("text-anchor", "middle")
        .style("fill", "white")
        .style("font", "9px sans-serif");

    // Render remaining axis plot elements  
    // X axis
    svg.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x));

    // Text label for the x axis
    svg.append("text")             
        .attr("transform",
            "translate(" + ((width - hist_dim - margin.between)/2) + " ," + 
                            (height + margin.top + margin.between + margin.bottom/2) + ")")
        .style("text-anchor", "middle")
        .text(home_abb + " Goals")
        .style("font", "14px sans-serif");

    // Y axis
    svg.append("g")
        .call(d3.axisLeft(y));

    // Text label for the y axis
    svg.append("text")       
        .attr("transform", "rotate(-90)")
        .attr("y", - margin.left/2)
        .attr("x", 0 - height/2 - hist_dim/2)
        .style("text-anchor", "middle")
        .text(away_abb + " Goals")
        .style("font", "14px sans-serif");        
}
