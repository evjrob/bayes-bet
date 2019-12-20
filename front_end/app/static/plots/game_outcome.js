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
        value: d.value,
        // want the cumulative to prior value (start of rect)
        cumulative: cumulative - d.value,
        percent: percent(d.value)
      }
    }).filter(d => d.value > 0)
    return _data
}
  
  //Read the data
function plot_game_outcome(data, target_div, home_abb, away_abb) {
    var config = {
        f: d3.format('.2f'),
        margin: {top: 25, right: 70, bottom: 20, left: 50},
        width: 700,
        height: 100,
        barHeight: 30,
        color_classes: {
            "away":["color-away", "color-away-light"],
            "home":["color-home", "color-home-light"]
        }
    }

    const { f, margin, width, height, barHeight, color_classes } = config
    const w = width - margin.left - margin.right
    const h = height - margin.top - margin.bottom
    const halfBarHeight = barHeight / 2
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
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')

    // stack rect for each data value
    selection.selectAll('rect_away')
        .data(_data_away)
        .enter().append('rect')
        .attr('class', 'rect-stacked')
        .attr('x', d => xScale(d.cumulative))
        .attr('y', away_y_pos)
        .attr('height', barHeight)
        .attr('width', d => xScale(d.value))
        .attr('class', (d, i) => color_classes.away[i])

    // add values on bar
    selection.selectAll('.text-value-away')
        .data(_data_away)
        .enter().append('text')
        .attr('class', 'text-value-away')
        .attr('text-anchor', 'middle')
        .attr('x', d => xScale(d.cumulative) + (xScale(d.value) / 2))
        .attr('y', away_y_pos + halfBarHeight + 5)
        .text(d => f(d.value * 100.0) + '%')
        .style("font", "11px sans-serif");

    // stack rect for each data value
    selection.selectAll('rect_home')
        .data(_data_home)
        .enter().append('rect')
        .attr('class', 'rect-stacked')
        .attr('x', d => xScale(d.cumulative))
        .attr('y', home_y_pos)
        .attr('height', barHeight)
        .attr('width', d => xScale(d.value))
        .attr('class', (d, i) => color_classes.home[i])

    // add values on bar
    selection.selectAll('.text-value-home')
        .data(_data_home)
        .enter().append('text')
        .attr('class', 'text-value-home')
        .attr('text-anchor', 'middle')
        .attr('x', d => xScale(d.cumulative) + (xScale(d.value) / 2))
        .attr('y', home_y_pos + halfBarHeight + 5)
        .text(d => f(d.value * 100.0) + '%')
        .style("font", "11px sans-serif");

    // team labels
    selection.append("text")
        .attr('class', 'away-win')
        .attr('text-anchor', 'left')
        .attr('x', -50)
        .attr('y', away_y_pos + halfBarHeight + 5)
        .text(!(home_win_pred) ? prediction_marker : "")
        .style("font", "14px sans-serif")
        .style("font-weight", !(home_win_pred) ? "bold" : "normal")
        .style("fill", prediction_colour);
    
    selection.append("text")
        .attr('class', 'away-labe')
        .attr('text-anchor', 'middle')
        .attr('x', -20)
        .attr('y', away_y_pos + halfBarHeight + 5)
        .text(away_abb)
        .style("font", "12px sans-serif")
        .style("font-weight", !(home_win_pred) ? "bold" : "normal");;

    selection.append("text")
        .attr('class', 'home-win')
        .attr('text-anchor', 'left')
        .attr('x', -50)
        .attr('y', home_y_pos + halfBarHeight + 5)
        .text((home_win_pred) ? prediction_marker : "")
        .style("font", "14px sans-serif")
        .style("font-weight", (home_win_pred) ? "bold" : "normal")
        .style("fill", prediction_colour);

    selection.append("text")
        .attr('class', 'home-label')
        .attr('text-anchor', 'middle')
        .attr('x', -20)
        .attr('y', home_y_pos + halfBarHeight + 5)
        .text(home_abb)
        .style("font", "12px sans-serif")
        .style("font-weight", (home_win_pred === true) ? "bold" : "normal");;

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
        .attr('y', -5)
        .text("Predited Win Probability (Regulation / Overtime)")
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
        .attr('y', -5)
        .text("Score")
        .style("font", "12px sans-serif")
        .style("font-weight", "bold");

    // 

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
}