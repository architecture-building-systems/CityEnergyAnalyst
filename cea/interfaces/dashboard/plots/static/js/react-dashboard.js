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
  Empty,
  Form,
  Menu,
  Dropdown
} = antd;
const { useState, useEffect, useCallback, useMemo, useRef } = React;
const { Provider, connect, useSelector, useDispatch } = ReactRedux;

const INITIAL_DASHBOARD = 0;
const defaultPlotStyle = {
  height: "calc(50vh - 125px)",
  minHeight: 300,
  margin: 5
};

// --------------------------
// Components
// --------------------------

const Dashboard = () => {
  const _fetchDashboards = useSelector(
    state => state.dashboard.fetchDashboards
  );
  const [dashboards, setDashboards] = useState([]);
  const [dashIndex, setDashIndex] = useState(INITIAL_DASHBOARD);
  const dispatch = useDispatch();

  const showModalNewDashboard = () =>
    dispatch(setModalNewDashboardVisibility(true));

  const handleSelect = useCallback(index => {
    setDashIndex(index);
  }, []);

  useEffect(() => {
    if (_fetchDashboards) {
      axios.get("http://localhost:5050/api/dashboard/").then(response => {
        setDashboards(response.data);
        dispatch(fetchDashboards(false));
      });
    }
  }, [_fetchDashboards]);

  if (!dashboards.length) return null;

  const { layout, plots } = dashboards[dashIndex];
  const dashboardNames = dashboards.map(dashboard => dashboard.name);

  return (
    <React.Fragment>
      <div id="cea-dashboard-content" style={{ minHeight: "100%" }}>
        <div id="cea-dashboard-content-title" style={{ margin: 5 }}>
          <DashSelect
            setDashIndex={handleSelect}
            dashboardNames={dashboardNames}
          />
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
              Duplicate Dashboard
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
      <ModalNewDashboard setDashIndex={handleSelect} />
      <ModalAddPlot />
      <ModalChangePlot />
      <ModalEditParameters />
      <ModalDeletePlot />
    </React.Fragment>
  );
};

const DashSelect = React.memo(({ setDashIndex, dashboardNames }) => {
  return (
    <Affix offsetTop={30}>
      <Select
        defaultValue={INITIAL_DASHBOARD}
        style={{ width: 200 }}
        onChange={value => setDashIndex(value)}
      >
        {dashboardNames.map((name, index) => (
          <option key={index} value={index}>
            {name}
          </option>
        ))}
      </Select>
    </Affix>
  );
});

// --------------------------
// Modal
// --------------------------

const ModalNewDashboard = React.memo(() => {
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
});

const ModalAddPlot = React.memo(() => {
  const [categories, setCategories] = useState(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [values, setValues] = useState({ category: null, plot_id: null });
  const visible = useSelector(state => state.dashboard.showModalAddPlot);
  const { dashIndex, index } = useSelector(state => state.dashboard.activePlot);
  const dispatch = useDispatch();

  const handleValue = useCallback(values => setValues(values), []);

  const handleOk = e => {
    setConfirmLoading(true);
    axios
      .post(
        `http://localhost:5050/api/dashboard/add-plot/${dashIndex}/${index}`,
        values
      )
      .then(response => {
        if (response) {
          console.log(response.data);
          dispatch(fetchDashboards(true));
          setConfirmLoading(false);
          dispatch(setModalAddPlotVisibility(false));
        }
      })
      .catch(error => {
        setConfirmLoading(false);
        console.log(error.response);
      });
  };

  const handleCancel = e => {
    dispatch(setModalAddPlotVisibility(false));
  };

  useEffect(() => {
    if (visible) {
      axios
        .get("http://localhost:5050/api/dashboard/plot-categories")
        .then(response => {
          setCategories(response.data);
        });
    } else setCategories(null);
  }, [visible]);

  return (
    <Modal
      title="Add plot"
      visible={visible}
      width={800}
      onOk={handleOk}
      onCancel={handleCancel}
      okButtonProps={{ disabled: categories === null }}
      confirmLoading={confirmLoading}
    >
      <CategoriesForm categories={categories} setValues={handleValue} />
    </Modal>
  );
});

const ModalChangePlot = React.memo(() => {
  const [categories, setCategories] = useState(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [values, setValues] = useState({ category: null, plot_id: null });
  const visible = useSelector(state => state.dashboard.showModalChangePlot);
  const { dashIndex, index } = useSelector(state => state.dashboard.activePlot);
  const dispatch = useDispatch();

  const handleValue = useCallback(values => setValues(values), []);

  const handleOk = e => {
    setConfirmLoading(true);
    axios
      .post(
        `http://localhost:5050/api/dashboard/change-plot/${dashIndex}/${index}`,
        values
      )
      .then(response => {
        if (response) {
          console.log(response.data);
          dispatch(fetchDashboards(true));
          setConfirmLoading(false);
          dispatch(setModalChangePlotVisibility(false));
        }
      })
      .catch(error => {
        setConfirmLoading(false);
        console.log(error.response);
      });
  };

  const handleCancel = e => {
    dispatch(setModalChangePlotVisibility(false));
  };

  useEffect(() => {
    if (visible) {
      axios
        .get("http://localhost:5050/api/dashboard/plot-categories")
        .then(response => {
          setCategories(response.data);
        });
    } else setCategories(null);
  }, [visible]);

  return (
    <Modal
      title="Change Plot"
      visible={visible}
      width={800}
      onOk={handleOk}
      onCancel={handleCancel}
      okButtonProps={{ disabled: categories === null }}
      confirmLoading={confirmLoading}
    >
      <CategoriesForm categories={categories} setValues={handleValue} />
    </Modal>
  );
});

const CategoriesForm = Form.create()(({ categories, setValues }) => {
  if (categories === null) return null;

  const categoryIDs = Object.keys(categories);
  const [selected, setSelected] = useState({
    category: categoryIDs[0],
    plots: categories[categoryIDs[0]].plots,
    selectedPlot: categories[categoryIDs[0]].plots[0].id
  });

  const handleCategoryChange = value => {
    setValues({ category: value, plot_id: categories[value].plots[0].id });
    setSelected({
      category: value,
      plots: categories[value].plots,
      selectedPlot: categories[value].plots[0].id
    });
  };

  const handlePlotChange = value => {
    setValues({ category: selected.category, plot_id: value });
    setSelected({ ...selected, selectedPlot: value });
  };

  useEffect(() => {
    if (categories !== null)
      setValues({
        category: selected.category,
        plot_id: selected.selectedPlot
      });
  }, [categories]);

  return (
    <Form layout="vertical">
      <Form.Item label="Category" key="category">
        <Select defaultValue={categoryIDs[0]} onChange={handleCategoryChange}>
          {categoryIDs.map(id => (
            <Option key={id} value={id}>
              {categories[id].label}
            </Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item label="Plot" key="plot">
        <Select value={selected.selectedPlot} onChange={handlePlotChange}>
          {selected.plots.map(plot => (
            <Option key={plot.id} value={plot.id}>
              {plot.name}
            </Option>
          ))}
        </Select>
      </Form.Item>
    </Form>
  );
});

const ModalEditParameters = React.memo(() => {
  const [parameters, setParameters] = useState(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const visible = useSelector(state => state.dashboard.showModalEditParameters);
  const { dashIndex, index } = useSelector(state => state.dashboard.activePlot);
  const formRef = useRef();
  const dispatch = useDispatch();

  const handleOk = e => {
    formRef.current.validateFields((err, values) => {
      if (!err) {
        setConfirmLoading(true);
        console.log("Received values of form: ", values);
        axios
          .post(
            `http://localhost:5050/api/dashboard/plot-parameters/${dashIndex}/${index}`,
            values
          )
          .then(response => {
            if (response) {
              console.log(response.data);
              dispatch(fetchDashboards(true));
              setConfirmLoading(false);
              dispatch(setModalEditParametersVisibility(false));
            }
          })
          .catch(error => {
            setConfirmLoading(false);
            console.log(error.response);
          });
      }
    });
  };

  const handleCancel = e => {
    dispatch(setModalEditParametersVisibility(false));
  };

  useEffect(() => {
    if (visible) {
      axios
        .get(
          `http://localhost:5050/api/dashboard/plot-parameters/${dashIndex}/${index}`
        )
        .then(response => {
          setParameters(response.data);
        });
    }
  }, [dashIndex, index]);

  useEffect(() => {
    setParameters(null);
  }, [visible]);

  return (
    <Modal
      title="Edit plot parameters"
      visible={visible}
      width={800}
      onOk={handleOk}
      onCancel={handleCancel}
      okButtonProps={{ disabled: parameters === null }}
      confirmLoading={confirmLoading}
    >
      <ParamsForm ref={formRef} parameters={parameters} />
    </Modal>
  );
});

const ParamsForm = Form.create()(({ parameters, form }) => {
  const { getFieldDecorator } = form;

  return (
    <Form layout="horizontal">
      {parameters
        ? parameters.map(param => ceaParameter(param, getFieldDecorator))
        : "Fetching Data..."}
    </Form>
  );
});

const ModalDeletePlot = React.memo(() => {
  const [confirmLoading, setConfirmLoading] = useState(false);
  const visible = useSelector(state => state.dashboard.showModalDeletePlot);
  const { dashIndex, index } = useSelector(state => state.dashboard.activePlot);
  const dispatch = useDispatch();

  const handleOk = e => {
    setConfirmLoading(true);
    axios
      .post(
        `http://localhost:5050/api/dashboard/delete-plot/${dashIndex}/${index}`
      )
      .then(response => {
        if (response) {
          console.log(response.data);
          dispatch(fetchDashboards(true));
          setConfirmLoading(false);
          dispatch(setModalDeletePlotVisibility(false));
        }
      })
      .catch(error => {
        setConfirmLoading(false);
        console.log(error.response);
      });
  };

  const handleCancel = e => {
    dispatch(setModalDeletePlotVisibility(false));
  };

  return (
    <Modal
      title="Delete plot"
      visible={visible}
      width={800}
      onOk={handleOk}
      onCancel={handleCancel}
      confirmLoading={confirmLoading}
      okText="Delete"
      okButtonProps={{ type: "danger" }}
    >
      Are you sure you want to delete this plot?
    </Modal>
  );
});

// --------------------------
// Layouts
// --------------------------

const RowLayout = ({ dashIndex, plots }) => {
  const dispatch = useDispatch();

  const showModalAddPlot = () =>
    dispatch(setModalAddPlotVisibility(true, dashIndex, plots.length + 1));

  return (
    <React.Fragment>
      {plots.length ? (
        plots.map((data, index) => (
          <Row key={`${dashIndex}-${index}-${data.hash}`}>
            <Col>
              <Plot index={index} dashIndex={dashIndex} data={data} />
            </Col>
          </Row>
        ))
      ) : (
        <Row>
          <Col>
            <EmptyPlot dashIndex={dashIndex} index={0} />
          </Col>
        </Row>
      )}

      {plots.length ? (
        <Affix offsetBottom={100}>
          <Button
            type="primary"
            icon="plus"
            style={{ float: "right", marginTop: 20 }}
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

  return (
    <React.Fragment>
      <div className="row display-flex">
        {plots.map((data, index) => (
          <div
            className="col-lg-4 col-md-12 col-sm-12 col-xs-12 plot-widget"
            key={`${dashIndex}-${index}-${data.hash}`}
          >
            {data.plot !== "empty" ? (
              <Plot index={index} dashIndex={dashIndex} data={data} />
            ) : (
              <EmptyPlot dashIndex={dashIndex} index={index} />
            )}
          </div>
        ))}
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
          <EmptyPlot dashIndex={dashIndex} index={5 + i} />
        </div>
      );
    }
  }

  return (
    <React.Fragment>
      <div className="row display-flex">
        {plots.map((data, index) => (
          <div
            className={`col-lg-${
              index === 0 ? 8 : 4
            } col-md-12 col-sm-12 col-xs-12 plot-widget`}
            key={`${dashIndex}-${index}-${data.hash}`}
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
  const dispatch = useDispatch();

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
      extra={<EditMenu dashIndex={dashIndex} index={index} />}
      style={{ ...plotStyle, height: "", minHeight: "" }}
      headStyle={{ height: 45 }}
      bodyStyle={{ height: plotStyle.height, minHeight: plotStyle.minHeight }}
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

const EditMenu = React.memo(({ dashIndex, index }) => {
  const dispatch = useDispatch();

  const showModalEditParameters = () =>
    dispatch(setModalEditParametersVisibility(true, dashIndex, index));

  const showModalChangePlot = () =>
    dispatch(setModalChangePlotVisibility(true, dashIndex, index));

  const showModalDeletePlot = () =>
    dispatch(setModalDeletePlotVisibility(true, dashIndex, index));

  const menu = (
    <Menu>
      <Menu.Item key="changePlot" onClick={showModalChangePlot}>
        Change Plot
      </Menu.Item>
      <Menu.Item key="editParameters" onClick={showModalEditParameters}>
        Edit Parameters
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="deletePlot" onClick={showModalDeletePlot}>
        <div style={{ color: "red" }}>Delete Plot</div>
      </Menu.Item>
    </Menu>
  );

  return (
    <React.Fragment>
      <Dropdown overlay={menu} trigger={["click"]}>
        <a className="ant-dropdown-link">
          Edit <Icon type="down" />
        </a>
      </Dropdown>
    </React.Fragment>
  );
});

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

const EmptyPlot = ({ style, dashIndex, index }) => {
  const dispatch = useDispatch();
  const showModalAddPlot = () =>
    dispatch(setModalAddPlotVisibility(true, dashIndex, index));

  const plotStyle = { ...defaultPlotStyle, ...style };

  return (
    <Card
      title="Empty Plot"
      style={{ ...plotStyle, height: "", minHeight: "" }}
      headStyle={{ height: 45 }}
      bodyStyle={{ height: plotStyle.height, minHeight: plotStyle.minHeight }}
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

const FETCH_DASHBOARDS = "FETCH_DASHBOARDS";
const fetchDashboards = fetch => {
  return {
    type: FETCH_DASHBOARDS,
    payload: { fetchDashboards: fetch }
  };
};

const SHOW_MODAL_NEW_DASHBOARD = "SHOW_MODAL_NEW_DASHBOARD";
const setModalNewDashboardVisibility = visible => {
  return {
    type: SHOW_MODAL_NEW_DASHBOARD,
    payload: { showModalNewDashboard: visible }
  };
};

const SHOW_MODAL_ADD_PLOT = "SHOW_MODAL_ADD_PLOT";
const setModalAddPlotVisibility = (visible, dashIndex, index) => {
  return {
    type: SHOW_MODAL_ADD_PLOT,
    payload: { showModalAddPlot: visible, activePlot: { dashIndex, index } }
  };
};

const SHOW_MODAL_CHANGE_PLOT = "SHOW_MODAL_CHANGE_PLOT";
const setModalChangePlotVisibility = (visible, dashIndex, index) => {
  return {
    type: SHOW_MODAL_CHANGE_PLOT,
    payload: { showModalChangePlot: visible, activePlot: { dashIndex, index } }
  };
};

const SHOW_MODAL_EDIT_PARAMETERS = "SHOW_MODAL_EDIT_PARAMETERS";
const setModalEditParametersVisibility = (visible, dashIndex, index) => {
  return {
    type: SHOW_MODAL_EDIT_PARAMETERS,
    payload: {
      showModalEditParameters: visible,
      activePlot: { dashIndex, index }
    }
  };
};

const SHOW_MODAL_DELETE_PLOT = "SHOW_MODAL_DELETE_PLOT";
const setModalDeletePlotVisibility = (visible, dashIndex, index) => {
  return {
    type: SHOW_MODAL_DELETE_PLOT,
    payload: {
      showModalDeletePlot: visible,
      activePlot: { dashIndex, index }
    }
  };
};

// --------------------------
// Reducer
// --------------------------

const initialState = {
  fetchDashboards: true,
  showModalNewDashboard: false,
  showModalAddPlot: false,
  showModalChangePlot: false,
  showModalEditParameters: false,
  showModalDeletePlot: false,
  activePlot: { dashIndex: null, index: null }
};

const dashboard = (state = initialState, { type, payload }) => {
  switch (type) {
    case FETCH_DASHBOARDS:
      return { ...state, ...payload };
    case SHOW_MODAL_NEW_DASHBOARD:
      return { ...state, ...payload };
    case SHOW_MODAL_ADD_PLOT:
      return { ...state, ...payload };
    case SHOW_MODAL_CHANGE_PLOT:
      return { ...state, ...payload };
    case SHOW_MODAL_EDIT_PARAMETERS:
      return { ...state, ...payload };
    case SHOW_MODAL_DELETE_PLOT:
      return { ...state, ...payload };
    default:
      return state;
  }
};

// --------------------------
// Redux
// --------------------------

const rootReducer = Redux.combineReducers({ dashboard });
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
