const {
  Spin,
  Icon,
  Button,
  Row,
  Col,
  Select,
  Card,
  Affix,
  Modal,
  Result,
  Empty
} = antd;
const { useState, useEffect, useCallback, useMemo } = React;
const { Provider, connect, useSelector, useDispatch } = ReactRedux;

const INITIAL_DASHBOARD = 0;
const defaultPlotStyle = { height: 350, margin: 5 };

// --------------------------
// Components
// --------------------------

const Dashboard = () => {
  const [dashboards, setDashboards] = useState([]);
  const [dashIndex, setDashIndex] = useState(INITIAL_DASHBOARD);
  const dispatch = useDispatch();

  const showModalNewDashboard = () =>
    dispatch(setModalNewDashboardVisibility(true));

  const handleSelect = useCallback(index => {
    setDashIndex(index);
  }, []);

  useEffect(() => {
    axios
      .get("http://localhost:5050/api/dashboard/")
      .then(response => setDashboards(response.data));
  }, []);

  if (!dashboards.length) return null;

  const { layout, plots } = dashboards[dashIndex];

  return (
    <React.Fragment>
      <div id="cea-dashboard-content" style={{ minHeight: "100%" }}>
        <div id="cea-dashboard-content-title" style={{ margin: 5 }}>
          <DashSelect setDashIndex={handleSelect} dashboards={dashboards} />
          <div style={{ position: "absolute", left: 250, top: 18 }}>
            <Button
              type="primary"
              icon="plus"
              size="small"
              onClick={showModalNewDashboard}
            >
              New Dashboard
            </Button>
            <Button type="primary" icon="edit" size="small">
              Set Scenario
            </Button>
          </div>
        </div>
        <div id="cea-dashboard-layout">
          {layout === "row" ? (
            <RowLayout dashIndex={dashIndex} plots={plots} />
          ) : layout === "map" ? (
            <MapLayout dashIndex={dashIndex} plots={plots} />
          ) : (
            <GridLayout dashIndex={dashIndex} plots={plots} />
          )}
        </div>
      </div>
      <ModalNewDashboard />
    </React.Fragment>
  );
};

const DashSelect = ({ setDashIndex, dashboards }) => {
  const dashList = useMemo(
    () =>
      dashboards.map((dashboard, index) => (
        <option key={index} value={index}>
          {dashboard.name}
        </option>
      )),
    [dashboards]
  );

  return (
    <Affix offsetTop={30}>
      <Select
        defaultValue={INITIAL_DASHBOARD}
        style={{ width: 200 }}
        onChange={value => setDashIndex(value)}
      >
        {dashList}
      </Select>
    </Affix>
  );
};

// --------------------------
// Modal
// --------------------------

const ModalAddPlot = () => {
  const visible = useSelector(state => state.dashboard.showModalAddPlot);
  const dispatch = useDispatch();

  const handleOk = e => {
    dispatch(setModalAddPlotVisibility(false));
  };

  const handleCancel = e => {
    dispatch(setModalAddPlotVisibility(false));
  };

  return (
    <Modal
      title="Add plot"
      visible={visible}
      onOk={handleOk}
      onCancel={handleCancel}
    >
      <p>Some contents...</p>
    </Modal>
  );
};

const ModalNewDashboard = () => {
  const visible = useSelector(state => state.dashboard.showModalNewDashboard);
  const dispatch = useDispatch();

  const handleOk = e => {
    dispatch(setModalNewDashboardVisibility(false));
  };

  const handleCancel = e => {
    dispatch(setModalNewDashboardVisibility(false));
  };

  return (
    <Modal
      title="New Dashboard"
      visible={visible}
      onOk={handleOk}
      onCancel={handleCancel}
    >
      <p>Some contents...</p>
    </Modal>
  );
};

// --------------------------
// Layouts
// --------------------------

const RowLayout = ({ dashIndex, plots }) => {
  const dispatch = useDispatch();

  const showModalAddPlot = () => dispatch(setModalAddPlotVisibility(true));

  return (
    <React.Fragment>
      <ModalAddPlot />
      {plots.length ? (
        plots.map((data, index) => (
          <Row key={`${dashIndex}-${index}`}>
            <Col>
              <Plot index={index} dashIndex={dashIndex} data={data} />
            </Col>
          </Row>
        ))
      ) : (
        <Row>
          <Col>
            <EmptyPlot />
          </Col>
        </Row>
      )}

      {plots.length ? (
        <Affix offsetBottom={100}>
          <Button
            type="primary"
            icon="plus"
            style={{ float: "right" }}
            onClick={showModalAddPlot}
          >
            Add plot
          </Button>
        </Affix>
      ) : null}
    </React.Fragment>
  );
};

const GridLayout = ({ dashIndex, plots }) => {
  if (!plots.length) return <h1>No plots found</h1>;

  const emptyplots = [];
  if (plots.length < 6) {
    for (var i = 0; i < 6 - plots.length; i++) {
      emptyplots.push(
        <div
          className="col-lg-4 col-md-12 col-sm-12 col-xs-12 plot-widget"
          key={`${dashIndex}-${i}`}
        >
          <EmptyPlot />
        </div>
      );
    }
  }

  return (
    <React.Fragment>
      <ModalAddPlot />
      <div className="row display-flex">
        {plots.map((data, index) => (
          <div
            className="col-lg-4 col-md-12 col-sm-12 col-xs-12 plot-widget"
            key={`${dashIndex}-${index}`}
          >
            <Plot index={index} dashIndex={dashIndex} data={data} />
          </div>
        ))}
        {emptyplots}
      </div>
    </React.Fragment>
  );
};

const MapLayout = ({ dashIndex, plots }) => {
  if (!plots.length) return <h1>No plots found</h1>;

  const emptyplots = [];
  if (plots.length < 5) {
    for (var i = 0; i < 5 - plots.length; i++) {
      emptyplots.push(
        <div
          className="col-lg-4 col-md-12 col-sm-12 col-xs-12 plot-widget"
          key={`${dashIndex}-${5 + i}`}
        >
          <EmptyPlot />
        </div>
      );
    }
  }

  return (
    <React.Fragment>
      <ModalAddPlot />
      <div className="row display-flex">
        {plots.map((data, index) => (
          <div
            className={`col-lg-${
              index === 0 ? 8 : 4
            } col-md-12 col-sm-12 col-xs-12 plot-widget`}
            key={`${dashIndex}-${index}`}
          >
            <Plot index={index} dashIndex={dashIndex} data={data} />
          </div>
        ))}
        {emptyplots}
      </div>
    </React.Fragment>
  );
};

// --------------------------
// Plots
// --------------------------

const Plot = ({ index, dashIndex, data, style }) => {
  const [div, setDiv] = useState(null);
  const [error, setError] = useState(null);
  const [hasIntersected, setIntersected] = useState(false);

  const plotStyle = { ...defaultPlotStyle, ...style };

  // TODO: Maybe find a better solution
  const hash = `cea-react-${data.hash}`;

  // Get plot div
  useEffect(() => {
    let mounted = true;
    const source = axios.CancelToken.source();
    axios
      .get(`http://localhost:5050/plots/div/${dashIndex}/${index}`, {
        cancelToken: source.token
      })
      .then(response => {
        if (mounted)
          setDiv(() => {
            let script = null;
            let content = HTMLReactParser(response.data, {
              replace: function(domNode) {
                if (domNode.type === "script" && domNode.children[0]) {
                  script = domNode.children[0].data;
                }
              }
            });
            return { content, script };
          });
      })
      .catch(_error => {
        setError(_error.response);
      });

    return () => {
      // Cancel the request if it is not completed
      mounted = false;
      source.cancel();

      // Clean up script node if it is mounted
      let script = document.querySelector(`script[data-id=script-${hash}]`);
      if (script) script.remove();
    };
  }, []);

  // Mount script node when div is mounted
  useEffect(() => {
    if (div) {
      var _script = document.createElement("script");
      _script.dataset.id = `script-${hash}`;
      document.body.appendChild(_script);
      _script.append(div.script);
    }
  }, [div]);

  return (
    <Card
      title={
        <div>
          <span style={{ fontWeight: "bold" }}>{data.title}</span>
          {data.parameters["scenario-name"] && (
            <React.Fragment>
              <span> - </span>
              <small>{data.parameters["scenario-name"]}</small>
            </React.Fragment>
          )}
        </div>
      }
      extra={null}
      style={{ ...plotStyle, height: "" }}
      bodyStyle={{ height: plotStyle.height }}
      size="small"
    >
      {div ? (
        div.content
      ) : error ? (
        <ErrorPlot error={error} />
      ) : (
        <LoadingPlot plotStyle={plotStyle} />
      )}
    </Card>
  );
};

const LoadingPlot = ({ plotStyle }) => {
  return (
    <Spin
      indicator={<Icon type="loading" style={{ fontSize: 24 }} spin />}
      tip="Loading Plot..."
    >
      <div style={{ height: plotStyle.height }} />
    </Spin>
  );
};

const ErrorPlot = ({ error }) => {
  console.log(error.status);
  if (error.status === 404) return HTMLReactParser(error.data);
  if (error.status === 500)
    return (
      <React.Fragment>
        <div style={{ textAlign: "center" }}>
          <h3>Something went wrong!</h3>
        </div>
        <pre style={{ height: 200, fontSize: 10, overflow: "auto" }}>
          {error.data}
        </pre>
      </React.Fragment>
    );
  return null;
};

const EmptyPlot = ({ style }) => {
  const dispatch = useDispatch();
  const showModalAddPlot = () => dispatch(setModalAddPlotVisibility(true));

  const plotStyle = { ...defaultPlotStyle, ...style };

  return (
    <Card
      title="Empty Plot"
      style={{ ...plotStyle, height: "" }}
      bodyStyle={{ height: plotStyle.height }}
      size="small"
    >
      <Empty>
        <Button type="primary" icon="plus" onClick={showModalAddPlot}>
          Add plot
        </Button>
      </Empty>
    </Card>
  );
};

// --------------------------
// Actions
// --------------------------

const SHOW_MODAL_NEW_DASHBOARD = "SHOW_MODAL_NEW_DASHBOARD";
const setModalNewDashboardVisibility = visible => {
  return {
    type: SHOW_MODAL_NEW_DASHBOARD,
    payload: { showModalNewDashboard: visible }
  };
};

const SHOW_MODAL_ADD_PLOT = "SHOW_MODAL_ADD_PLOT";
const setModalAddPlotVisibility = visible => {
  return {
    type: SHOW_MODAL_ADD_PLOT,
    payload: { showModalAddPlot: visible }
  };
};

// --------------------------
// Reducer
// --------------------------

const initialState = { showModalNewDashboard: false, showModalAddPlot: false };

const dashboard = (state = initialState, { type, payload }) => {
  switch (type) {
    case SHOW_MODAL_NEW_DASHBOARD:
      return { ...state, ...payload };
    case SHOW_MODAL_ADD_PLOT:
      return { ...state, ...payload };
    default:
      return state;
  }
};

// --------------------------
// Redux
// --------------------------

const rootReducer = Redux.combineReducers({
  dashboard
});
const store = Redux.createStore(
  rootReducer,
  window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__()
);

ReactDOM.render(
  <Provider store={store}>
    <Dashboard />
  </Provider>,
  document.querySelector("#cea-dashboard")
);

// To enable resize of Plotly plots
window.addEventListener("resize", function() {
  console.log("resizing");
  $.each($(".plotly-graph-div.js-plotly-plot"), function() {
    Plotly.Plots.resize($(this).attr("id"));
  });
});

document.getElementById("menu_toggle").addEventListener("click", function() {
  console.log("resizing");
  $.each($(".plotly-graph-div.js-plotly-plot"), function() {
    Plotly.Plots.resize($(this).attr("id"));
  });
});
