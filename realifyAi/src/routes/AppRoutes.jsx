import React, { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import PageLoader from '@/components/feedback/PageLoader';
import { routes } from '@/routes/routeConfig';

/** Renders one entry and, recursively, any nested children it declares. */
const renderRoute = ({ path, index, element, children }, key) => (
  <Route key={key} {...(index ? { index: true } : { path })} element={element}>
    {children?.map((childRoute, i) => renderRoute(childRoute, `${key}/${i}`))}
  </Route>
);

/** Renders the route registry. Route definitions live in routeConfig.jsx. */
const AppRoutes = () => (
  <Suspense fallback={<PageLoader />}>
    <Routes>
      {routes.map((route, i) => renderRoute(route, route.path ?? `index-${i}`))}
    </Routes>
  </Suspense>
);

export default AppRoutes;
