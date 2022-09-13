var barChart;
function createBar(data) {
  barChart = Highcharts.chart("bar", {
    chart: {
      type: "bar",
    },
    xAxis: {
      categories: data.x_axis
    },
    yAxis: {
      stackLabels: {
        enabled: true,
        style: {
          color: "#212529"
        }
      },
      title: {
        text: data.y_axis_label
      }
    },
    tooltip: {
      headerFormat: "<b>{point.x}</b><br/>",
      pointFormat: "{series.name}: {point.y}<br/>Total: {point.stackTotal}"
    },
    plotOptions: {
      series: {
        stacking: properties.stack,
      }
    },
    series: data.series
  });
}

var columnChart;
function createColumn(data) {
  columnChart = Highcharts.chart("column", {
    chart: {
      type: "column",
    },
    xAxis: {
      categories: data.x_axis
    },
    yAxis: {
      stackLabels: {
        enabled: true,
        style: {
          color: "#212529"
        }
      }
    },
    tooltip: {
      headerFormat: "<b>{point.x}</b><br/>",
      pointFormat: "{series.name}: {point.y}<br/>Total: {point.stackTotal}"
    },
    plotOptions: {
      series: {
        stacking: properties.stack,
      }
    },
    series: data.series
  });
}

var lineChart;
function createLine(data) {
  lineChart = Highcharts.chart("line", {
    xAxis: {
      categories: data.x_axis
    },
    tooltip: {
      headerFormat: "<b>{point.x}</b><br/>",
      pointFormat: "{series.name}: {point.y}<br/>Total: {point.stackTotal}"
    },
    plotOptions: {
      series: {
        marker: {
          enabled: false,
          symbol: "circle",
        }
      }
    },
    series: data.series
  });
};

var areaChart;
function createArea(data) {
  areaChart = Highcharts.chart("area", {
    chart: {
      type: "area"
    },
    xAxis: {
      categories: data.x_axis
    },
    tooltip: {
      headerFormat: "<b>{point.x}</b><br/>",
      pointFormat: "{series.name}: {point.y}<br/>Total: {point.stackTotal}"
    },
    plotOptions: {
      area: {
        stacking: "normal",
        lineColor: "#fcfcfc",
        lineWidth: 1,
        marker: {
          enabled: false,
          lineWidth: 1,
          lineColor: "#fcfcfc",
          symbol: "circle",
        }
      },
    },
    series: data.series
  });
};

var drilldownChart;
function createDrilldown(data) {
  drilldownChart = Highcharts.chart("drilldown", {
    chart: {
      type: "bar",
    },
    xAxis: {
      type: "category"
    },
    tooltip: {
      headerFormat: "<b>{point.name}</b>",
      pointFormat: "{point.y:.0f}"
    },
    plotOptions: {
      series: {
        borderWidth: 0,
        dataLabels: {
          enabled: true,
          format: "{point.y:.0f}"
        }
      }
    },
    series: [
      {
        name: "Series",
        data: data.top_level
      }
    ],
    drilldown: {
      series: data.series
    }
  });
};

// pie chart variables, global so we can use them later
let pieChart;
let pieData = [];
let piePeriods = [];
let pieCurrent = 0;
let pieLast = 0;

function createPie(data) {
  pieData = data.series;
  piePeriods = data.x_axis;

  pieChart = Highcharts.chart("pie", {
    chart: {
      plotBackgroundColor: null,
      plotBorderWidth: null,
      plotShadow: false,
      type: "pie"
    },
    tooltip: {
      pointFormat: "<b>{point.y:.0f}</b>"
    },
    plotOptions: {
      pie: {
        dataLabels: {
          enabled: false
        },
        showInLegend: true
      }
    },
    series: [{}]
  });

  $(".switch-pie").click(function() {
    let period = $(this).attr("data-period");
    openPie(period);
  })

  pieLast = piePeriods.length - 1;
  openPie(pieCurrent)
};

function openPie(period) {
  let periodValues = []

  $(pieData).each(function() {
    periodValues.push({
      name: this.name,
      y: this.data[period],
    });
  });

  pieChart.series[0].setData(periodValues);

  // various functions to update the toggles
  // to start, show current period in toggle menu
  $(".current-pie").text(piePeriods[period])

  let prevPeriod = Number(period) - 1;
  let nextPeriod = Number(period) + 1;

  // use this to update the buttons, making sure to disable them when on first or last period
  if (period == 0) {
    $(".prev-pie").addClass("disabled");
  } else {
    $(".prev-pie").removeClass("disabled").attr("data-period", prevPeriod);
  }

  if (period == pieLast) {
    $(".next-pie").addClass("disabled");
  } else {
    $(".next-pie").removeClass("disabled").attr("data-period", nextPeriod);
  }
}

// some variables we'll need later
let dataDefault;
let dataDrill;

let dataDefaultLoaded = false;
let dataDrillLoaded = false;

let barLoaded = false;
let columnLoaded = false;
let drilldownLoaded = false;
let lineLoaded = false;
let areaLoaded = false;
let pieLoaded = false;
let mapLoaded = false;

$(".item-visualisations .nav-link").click(function() {
  let nav = $(this);
  let tab = nav.data("tab");
  let viz = nav.data("viz");

  $(".item-visualisations .nav-link, .tab-content .tab-pane").removeClass("active");
  $(".tab-pane#" + tab).addClass("active");
  nav.addClass("active");

  if (nav.data("drilldown") == true) {
    if (dataDrillLoaded == false) {
      $.get(json_url + "?drilldown=true", function(data) {
        dataDrill = data;
        dataDrillLoaded = true;
        $(".tab-pane[data-drilldown='true']").removeClass("loading");
        createViz(viz)
      });
    } else {
      createViz(viz)
    }
  } else {
    if (dataDefaultLoaded == false) {
      $.get(json_url, function(data) {
        dataDefault = data;
        dataDefaultLoaded = true;
        $(".tab-pane[data-drilldown!='true']").removeClass("loading");
        createViz(viz)
      });
    } else {
      createViz(viz)
    }
  }
})

function createViz(viz) {
  if (viz == "bar" && barLoaded == false) {
    createBar(dataDefault);
    barLoaded = true
  } else if (viz == "column" && columnLoaded == false) {
    createColumn(dataDefault);
    columnLoaded = true
  } else if (viz == "drilldown" && drilldownLoaded == false) {
    createDrilldown(dataDrill)
    drilldownLoaded = true
  } else if (viz == "line" && lineLoaded == false) {
    createLine(dataDefault)
    lineLoaded = true
  } else if (viz == "area" && areaLoaded == false) {
    createArea(dataDefault)
    areaLoaded = true
  } else if (viz == "pie" && pieLoaded == false) {
    createPie(dataDefault)
    pieLoaded = true
  } else if (viz == "map" && mapLoaded == false) {
    createMap(dataDefault)
    mapLoaded = true
  }
}
