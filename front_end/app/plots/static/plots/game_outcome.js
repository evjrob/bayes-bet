// group data for chart and filter out zero values
function groupData(data) {
    // use scale to get percent values
    const percent = d3.scaleLinear()
      .domain([0, 100])
      .range([0, 100])
    // filter out data that has zero values
    // also get mapping for next placement
    // (save having to format data for d3 stack)
    let cumulative = 0
    const _data = data.map(d => {
      cumulative += d.value
      return {
        type: d.type,
        value: d.value,
        // want the cumulative to prior value (start of rect)
        cumulative: cumulative - d.value,
        percent: percent(d.value)
      }
    }).filter(d => d.value > 0)
    return _data
}

var LightenColor = function(color, percent) {
    var num = parseInt(color.replace("#",""), 16),
      amt = Math.round(2.55 * percent),
      R = (num >> 16) + amt,
      B = (num >> 8 & 0x00FF) + amt,
      G = (num & 0x0000FF) + amt,
      newR = (R<255?R<1?0:R:255)*0x10000,
      newB = (B<255?B<1?0:B:255)*0x100,
      newG = (G<255?G<1?0:G:255);

      return "#" + (0x1000000 + newR + newB + newG).toString(16).slice(1);
};
  
//Read the data
function plot_game_outcome(data, target_div, home_abb, home_colors, away_abb, away_colors) {

    var parent_div = d3.select(target_div);
    var min_width = 350;
    var max_width = 700;
    var div_width = Math.max(min_width, Math.min(max_width, parseInt(parent_div.style("width"))));

    var config = {
        f: d3.format('.2f'),
        margin: {top: 25, right: 70, bottom: 20, left: 100},
        width: div_width,
        height: 150,
        barHeight: 30,
        color_classes: {
            "away":["color-away", "color-away-mid", "color-away-light"],
            "home":["color-home", "color-home-mid", "color-home-light"]
        }
    }

    const { f, margin, width, height, barHeight, color_classes } = config
    const w = width - margin.left - margin.right
    const h = height - margin.top - margin.bottom
    const halfBarHeight = barHeight / 2
    const accentHeight = 5;
    const away_y_pos = 5;
    const home_y_pos = 10 + barHeight;

    const _data_home = groupData(data.predictions.home);
    const _data_away = groupData(data.predictions.away);

    const home_win_pred = d3.sum(data.predictions.home, d => d.value) >= 0.50;
    const prediction_correct = ((data.score.home > data.score.away) == home_win_pred);
    var prediction_marker = "*";
    var prediction_colour = "black";
    function get_pred_result() {
        if (data.score.home == "-") {
            prediction_marker = "*";
        } else if (prediction_correct) {
            prediction_marker =  "\u2714";
            prediction_colour = "green";
        } else {
            prediction_marker =  "\u2718";
            prediction_colour = "red";
        }
    }
    get_pred_result();

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
    };
    var mousemove = function(d) {
        if (d !== undefined) {
            var chart_pos = selection.node().getBoundingClientRect();
            var main_pos = d3.select('#main').node().getBoundingClientRect();
            tooltip
            .html(d.type + ' : ' + f(d.value * 100.0) + '%')
            .style("left", (d3.event.clientX - chart_pos.left - 30) + "px")
            .style("top", (d3.event.clientY - main_pos.top + 80) + "px")
        }
    };
    var mouseleave = function(d) {
        tooltip.style("opacity", 0)
    };

    var totalprob = function(d) {
        dvals = d.map(a => a.value);
        dsum = dvals.reduce((a,b) => a + b)
        return dsum
    }

    var probstr = function(p) {
        return f(p * 100) + '%'
    }

    var decimal_odds = function(a,b) {
        a_prob = totalprob(a);
        b_prob = totalprob(b);
        a_odds = 1 / a_prob;
        b_odds = 1 / b_prob;
        return [a_odds, b_odds]
    }

    var get_decimal_odds_string = function(away_abb, away_data, home_abb, home_data) {
        odds = decimal_odds(away_data, home_data);
        away_odds = odds[0];
        home_odds = odds[1];
        return away_abb + ' ' + f(away_odds) + ' : ' + f(home_odds) + ' ' + home_abb 
    };

    var get_american_odds_string = function(away_abb, away_data, home_abb, home_data) {
        odds = decimal_odds(away_data, home_data);
        away_odds = odds[0];
        home_odds = odds[1];
        if (away_odds >= 2) {
            away_odds = '+' + Math.round((away_odds - 1) * 100);
        } else {
            away_odds = Math.round(-100 / (away_odds - 1));
        }
        if (home_odds >= 2) {
            home_odds = '+' + Math.round((home_odds - 1) * 100);
        } else {
            home_odds = Math.round(-100 / (home_odds - 1));
        }
        return away_abb + ' ' + away_odds + ' : ' + home_odds + ' ' + home_abb 
    };

    // set up scales for horizontal placement
    const xScale = d3.scaleLinear()
        .domain([0, 1])
        .range([0, w])

    // create svg in passed in div
    const selection = d3.select(target_div)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    // stack rect for each away team data value
    selection.selectAll('rect_away')
        .data(_data_away)
        .enter().append('rect')
        .attr('class', 'rect-stacked')
        .attr('x', d => xScale(d.cumulative))
        .attr('y', away_y_pos)
        .attr('height', barHeight)
        .attr('width', d => xScale(d.value))
        .attr('fill', (d, i) => LightenColor(away_colors[0], i*12.5))
        .on("mouseover", mouseover)
        .on("mousemove", d => mousemove(d))
        .on("mouseleave", mouseleave);

    // stack rect for each away team accent color
    selection.selectAll('rect_away')
        .data(_data_away)
        .enter().append('rect')
        .attr('class', 'rect-stacked')
        .attr('x', d => xScale(d.cumulative))
        .attr('y', away_y_pos + barHeight - accentHeight)
        .attr('height', accentHeight)
        .attr('width', d => xScale(d.value))
        .attr('fill', (d, i) => LightenColor(away_colors[1], i*12.5))
        .on("mouseover", mouseover)
        .on("mousemove", d => mousemove(d))
        .on("mouseleave", mouseleave);

    // stack rect for each home team data value
    selection.selectAll('rect_home')
        .data(_data_home)
        .enter().append('rect')
        .attr('class', 'rect-stacked')
        .attr('x', d => xScale(d.cumulative))
        .attr('y', home_y_pos)
        .attr('height', barHeight)
        .attr('width', d => xScale(d.value))
        .attr('fill', (d, i) => LightenColor(home_colors[0], i*12.5))
        .on("mouseover", mouseover)
        .on("mousemove", d => mousemove(d))
        .on("mouseleave", mouseleave);

    // stack rect for each home team accent color
    selection.selectAll('rect_home')
        .data(_data_home)
        .enter().append('rect')
        .attr('class', 'rect-stacked')
        .attr('x', d => xScale(d.cumulative))
        .attr('y', home_y_pos + barHeight - accentHeight)
        .attr('height', accentHeight)
        .attr('width', d => xScale(d.value))
        .attr('fill', (d, i) => LightenColor(home_colors[1], i*12.5))
        .on("mouseover", mouseover)
        .on("mousemove", d => mousemove(d))
        .on("mouseleave", mouseleave);

    // team labels
    selection.append("text")
        .attr('class', 'away-win')
        .attr('text-anchor', 'left')
        .attr('x', -100)
        .attr('y', away_y_pos + halfBarHeight + 5)
        .text(!(home_win_pred) ? prediction_marker : "")
        .style("font", "14px sans-serif")
        .style("font-weight", !(home_win_pred) ? "bold" : "normal")
        .style("fill", prediction_colour);
    
    selection.append("text")
        .attr('class', 'away-label')
        .attr('text-anchor', 'middle')
        .attr('x', -71)
        .attr('y', away_y_pos + halfBarHeight + 5)
        .text(away_abb)
        .style("font", "12px sans-serif")
        .style("font-weight", !(home_win_pred) ? "bold" : "normal");

    selection.append("text")
        .attr('class', 'away-prob')
        .attr('text-anchor', 'middle')
        .attr('x', -27)
        .attr('y', away_y_pos + halfBarHeight + 5)
        .text(probstr(totalprob(_data_away)))
        .style("font", "12px sans-serif")
        .style("font-weight", !(home_win_pred === true) ? "bold" : "normal");

    selection.append("text")
        .attr('class', 'home-win')
        .attr('text-anchor', 'left')
        .attr('x', -100)
        .attr('y', home_y_pos + halfBarHeight + 5)
        .text((home_win_pred) ? prediction_marker : "")
        .style("font", "14px sans-serif")
        .style("font-weight", (home_win_pred) ? "bold" : "normal")
        .style("fill", prediction_colour);

    selection.append("text")
        .attr('class', 'home-label')
        .attr('text-anchor', 'middle')
        .attr('x', -71)
        .attr('y', home_y_pos + halfBarHeight + 5)
        .text(home_abb)
        .style("font", "12px sans-serif")
        .style("font-weight", (home_win_pred === true) ? "bold" : "normal");

    selection.append("text")
        .attr('class', 'home-prob')
        .attr('text-anchor', 'middle')
        .attr('x', -27)
        .attr('y', home_y_pos + halfBarHeight + 5)
        .text(probstr(totalprob(_data_home)))
        .style("font", "12px sans-serif")
        .style("font-weight", (home_win_pred === true) ? "bold" : "normal");

    // scores
    selection.append("text")
        .attr('class', 'away-score')
        .attr('text-anchor', 'middle')
        .attr('x', w + 30)
        .attr('y', away_y_pos + halfBarHeight + 5)
        .text(data.score.away)
        .style("font", "12px sans-serif")
        .style("font-weight", !(home_win_pred) ? "bold" : "normal");
    
    selection.append("text")
        .attr('class', 'home-score')
        .attr('text-anchor', 'middle')
        .attr('x', w + 30)
        .attr('y', home_y_pos + halfBarHeight + 5)
        .text(data.score.home)
        .style("font", "12px sans-serif")
        .style("font-weight", (home_win_pred) ? "bold" : "normal");

    // prediction data label
    selection.append("text")
        .attr('class', 'prediction-label')
        .attr('text-anchor', 'left')
        .attr('x', 5)
        .attr('y', -15)
        .text("Predited Win Probability")
        .style("font", "12px sans-serif")
        .style("font-weight", "bold");

    selection.append("text")
        .attr('class', 'prediction-label')
        .attr('text-anchor', 'left')
        .attr('x', 5)
        .attr('y', -3)
        .text("(Regulation / OT / SO)")
        .style("font", "12px sans-serif")
        .style("font-weight", "bold");

    // actual score data label
    selection.append("text")
        .attr('class', 'home-score')
        .attr('text-anchor', 'middle')
        .attr('x', w + 30)
        .attr('y', -15)
        .text("Actual")
        .style("font", "12px sans-serif")
        .style("font-weight", "bold");

    selection.append("text")
        .attr('class', 'home-score')
        .attr('text-anchor', 'middle')
        .attr('x', w + 30)
        .attr('y', -3)
        .text("Score")
        .style("font", "12px sans-serif")
        .style("font-weight", "bold");

    // 100% bars
    selection.append("line")
        .attr("x1", w)  //<<== change your code here
        .attr("y1", away_y_pos - 1)
        .attr("x2", w)  //<<== and here
        .attr("y2", away_y_pos + barHeight + 1)
        .style("stroke-width", 1)
        .style("stroke", "black")
        .style("fill", "none");

    // 100% bars
    selection.append("line")
        .attr("x1", w)  //<<== change your code here
        .attr("y1", home_y_pos - 1)
        .attr("x2", w)  //<<== and here
        .attr("y2", home_y_pos + barHeight + 1)
        .style("stroke-width", 1)
        .style("stroke", "black")
        .style("fill", "none");

    // Decimal Odds
    selection.append("text")
        .attr('class', 'prediction-label')
        .attr('text-anchor', 'middle')
        .attr('x', (width / 4) - margin.left)
        .attr('y', 95)
        .text("Decimal Odds")
        .style("font", "12px sans-serif")
        .style("font-weight", "bold");
    
    selection.append("text")
        .attr('class', 'prediction-label')
        .attr('text-anchor', 'middle')
        .attr('x', (width / 4) - margin.left)
        .attr('y', 112)
        .text(get_decimal_odds_string(away_abb, _data_away, home_abb, _data_home))
        .style("font", "12px sans-serif");

    // American Odds
    selection.append("text")
        .attr('class', 'prediction-label')
        .attr('text-anchor', 'middle')
        .attr('x', (3 * width / 4) - margin.left)
        .attr('y', 95)
        .text("American Odds")
        .style("font", "12px sans-serif")
        .style("font-weight", "bold");

    selection.append("text")
        .attr('class', 'prediction-label')
        .attr('text-anchor', 'middle')
        .attr('x', (3 * width / 4) - margin.left)
        .attr('y', 112)
        .text(get_american_odds_string(away_abb, _data_away, home_abb, _data_home))
        .style("font", "12px sans-serif");
}